import asyncio
from uuid import UUID

from taskiq import Context, TaskiqDepends

from app.agents.agent_factory import (
    create_document_comparison_agent,
)
from app.core.db.database import AsyncSessionLocal
from app.observability.logging import logger
from app.repositories.document_comparison_repository import (
    DocumentComparisonRepository,
)
from app.repositories.document_extraction_repository import DocumentExtractionRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_summary_repository import DocumentSummaryRepository
from app.schemas.document_comparison import ComparisonCriterion
from app.services.document_comparison_orchestration_service import (
    DocumentComparisonOrchestrationService,
)
from app.services.document_extraction_service import DocumentExtractionService
from app.services.document_summary_service import DocumentSummaryService
from app.workers.broker import broker
from app.workers.retry import should_fail_prerequisite

document_comparison_agent = create_document_comparison_agent()

comparison_semaphore = asyncio.Semaphore(1)


@broker.task
async def coordinate_document_comparisons(
        document_id_str: str,
) -> None:
    document_id = UUID(document_id_str)

    ready_comparisons = []

    async with AsyncSessionLocal() as db:
        service = DocumentComparisonOrchestrationService(
            db=db,
            summary_service=DocumentSummaryService(
                document_summary_repository=DocumentSummaryRepository(db),
                document_repository=DocumentRepository(db),
            ),
            extraction_service=DocumentExtractionService(
                document_extraction_repository=DocumentExtractionRepository(db),
                document_repository=DocumentRepository(db),
            ),
        )

        comparisons = (
            await service.comparison_repository
            .find_waiting_comparisons_by_document_id(
                document_id=document_id,
            )
        )

        for comparison in comparisons:
            transitioned = (
                await service.check_prerequisites_and_set_pending(
                    comparison_id=comparison.id,
                    generation_id=comparison.generation_id,
                )
            )

            if transitioned:
                ready_comparisons.append(
                    (comparison.id, comparison.generation_id)
                )

        await db.commit()

    for comparison_id, generation_id in ready_comparisons:
        try:
            await generate_document_comparison.kiq(
                str(comparison_id),
                str(generation_id),
            )

        except Exception as exc:
            logger.exception(
                "Failed to dispatch document comparison | "
                "comparison_id=%s | generation_id=%s",
                comparison_id,
                generation_id,
            )

            async with AsyncSessionLocal() as db:
                repository = DocumentComparisonRepository(db)

                await repository.set_dispatch_failed(
                    comparison_id=comparison_id,
                    generation_id=generation_id,
                    error_message=str(exc)[:4000],
                )

                await db.commit()


@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def generate_document_comparison(
        comparison_id_str: str,
        generation_id_str: str,
        context: Context = TaskiqDepends(),
):
    async with comparison_semaphore:
        return await _generate_document_comparison(
            comparison_id_str=comparison_id_str,
            generation_id_str=generation_id_str,
            context=context
        )


async def _mark_comparison_failed(
        comparison_id: UUID,
        generation_id: UUID,
        error_message: str,
) -> None:
    """
    Mark the current comparison generation as failed.

    A fresh database session is used because the session that encountered
    the original exception may have an invalid transaction.
    """
    async with AsyncSessionLocal() as db:
        repository = DocumentComparisonRepository(db)

        updated = await repository.set_failed(
            comparison_id=comparison_id,
            generation_id=generation_id,
            error_message=error_message,
        )

        await db.commit()

        if not updated:
            logger.warning(
                "Could not mark comparison %s as failed. "
                "Its generation or processing status may have changed.",
                comparison_id,
            )


async def _generate_document_comparison(
        comparison_id_str: str,
        generation_id_str: str,
        context: Context,
):
    comparison_id = UUID(comparison_id_str)
    generation_id = UUID(generation_id_str)

    try:
        # Phase 1: Claim the comparison and load its inputs.
        async with AsyncSessionLocal() as db:
            repository = DocumentComparisonRepository(db)

            comparison = await repository.claim_for_processing(
                comparison_id=comparison_id,
                generation_id=generation_id,
            )

            if comparison is None:
                logger.info(
                    "Comparison %s could not be claimed. "
                    "It may already be processing or have a stale generation.",
                    comparison_id,
                )
                return

            inputs = await repository.find_comparison_inputs(
                comparison_id=comparison_id,
            )

            criteria = [
                ComparisonCriterion(value)
                for value in comparison.criteria
            ]

            # Every document must have a completed summary and extraction.
            # Never send partial inputs to the comparison agent.
            inputs_are_complete = (
                    len(inputs) == len(comparison.items)
                    and all(
                item["summary"] and item["extraction"] is not None
                for item in inputs
            )
            )

            if not inputs_are_complete:
                error_message = (
                    "One or more documents are missing a completed "
                    "summary or structured extraction."
                )

                await repository.set_failed(
                    comparison_id=comparison_id,
                    generation_id=generation_id,
                    error_message=error_message,
                )
                await db.commit()

                logger.error(
                    "Comparison %s has incomplete prerequisite data.",
                    comparison_id,
                )
                return

            # Copy the data before closing the database session.
            documents = [
                {
                    "document_id": item["document_id"],
                    "document_title": (
                            item["document_title"] or "Untitled document"
                    ),
                    "summary": item["summary"],
                    "extraction": item["extraction"],
                }
                for item in inputs
            ]

            await db.commit()

        # Phase 2: Call the model without an open database session.
        response = await document_comparison_agent.compare(
            documents=documents,
            criteria=criteria,
        )

        # Phase 3: Persist the successful result.
        async with AsyncSessionLocal() as db:
            repository = DocumentComparisonRepository(db)

            result_data = response.model_dump(
                mode="json",
                exclude={"overview", "conclusion"},
            )

            updated = await repository.set_completed(
                comparison_id=comparison_id,
                generation_id=generation_id,
                overview=response.overview,
                conclusion=response.conclusion,
                result_data=result_data,
            )

            await db.commit()

            if not updated:
                logger.warning(
                    "Comparison %s result was not saved. "
                    "Its generation or processing status may have changed.",
                    comparison_id,
                )
                return

    except Exception as exc:
        if should_fail_prerequisite(exc, context):
            try:
                await _mark_comparison_failed(
                    comparison_id=comparison_id,
                    generation_id=generation_id,
                    error_message=str(exc)[:4000],
                )
            except Exception:
                logger.exception(
                    "Could not record failure for document comparison %s.",
                    comparison_id,
                )

        logger.exception(
            "Document comparison %s failed.",
            comparison_id,
        )
        # Preserve the original exception for Taskiq retries.
        raise

    logger.info(
        "Document comparison %s completed successfully.",
        comparison_id,
    )

    return response
