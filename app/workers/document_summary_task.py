import asyncio
from uuid import UUID

from taskiq import Context, TaskiqDepends

from app.agents.agent_factory import create_document_summarization_agent
from app.core.db.database import AsyncSessionLocal
from app.models.document import DocumentStatus
from app.observability.logging import logger
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_extraction_repository import DocumentExtractionRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_summary_repository import DocumentSummaryRepository
from app.services.document_comparison_orchestration_service import DocumentComparisonOrchestrationService
from app.services.document_extraction_service import DocumentExtractionService
from app.services.document_summary_service import DocumentSummaryService
from app.workers.broker import broker
from app.workers.document_comparison_task import coordinate_document_comparisons
from app.workers.retry import should_fail_prerequisite

document_summarization_agent = create_document_summarization_agent()

_summarization_semaphore = asyncio.Semaphore(1)


async def _run_summary_with_semaphore(
        document_id_str: str,
        generation_id_str: str,
        context: Context,
):
    """
    Execute one summary generation at a time
    within this worker process.
    """

    async with _summarization_semaphore:
        return await _generate_document_summary(
            document_id_str=document_id_str,
            generation_id_str=generation_id_str,
            context=context,
        )


# ==============================================================
# Taskiq task
# ==============================================================

@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def generate_document_summary(
        document_id_str: str,
        generation_id_str: str,
        context: Context = TaskiqDepends(),
):
    """
    Generate or regenerate a document summary asynchronously.
    """
    return await _run_summary_with_semaphore(
        document_id_str=document_id_str,
        generation_id_str=generation_id_str,
        context=context,
    )


# ==============================================================
# Summary generation implementation
# ==============================================================

async def _generate_document_summary(
        document_id_str: str,
        generation_id_str: str,
        context: Context,
):
    document_id = UUID(document_id_str)
    generation_id = UUID(generation_id_str)

    logger.info(
        "Starting summary generation. "
        "[document_id=%s, generation_id=%s]",
        document_id,
        generation_id,
    )

    # ==========================================================
    # Transaction 1: Validate document and claim generation
    # PENDING / FAILED -> PROCESSING
    # ==========================================================

    async with AsyncSessionLocal() as session:

        document_repository = DocumentRepository(session)
        summary_repository = DocumentSummaryRepository(session)
        extraction_repository = DocumentExtractionRepository(session)
        chunk_repository = DocumentChunkRepository(session)

        document = (
            await document_repository.find_document_by_id_for_processing(
                document_id=document_id,
            )
        )

        if document is None:
            logger.warning(
                "Document does not exist. "
                "Skipping summary generation. "
                "[document_id=%s]",
                document_id,
            )
            return

        if document.status != DocumentStatus.READY:
            logger.error(
                "Document is not ready for summarization. "
                "[document_id=%s, status=%s]",
                document_id,
                document.status,
            )
            return

        # Atomically claim only the requested generation.
        summary = await summary_repository.claim_for_processing(
            document_id=document_id,
            generation_id=generation_id,
        )

        if summary is None:
            logger.info(
                "Generation is no longer pending or was already claimed. "
                "Skipping. [document_id=%s, generation_id=%s]",
                document_id,
                generation_id,
            )
            return

        chunks = await chunk_repository.find_chunks_by_document_id(
            document_id=document_id,
        )

        if not chunks:
            error_message = f"Document has no chunks to summarize | document_id={document_id} | generation_id={generation_id}."

            logger.error(error_message)

            updated = await summary_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message=error_message,
            )

            await session.commit()

            if updated:
                comparison_service = DocumentComparisonOrchestrationService(
                    db=session,
                    summary_service=DocumentSummaryService(
                        document_repository=document_repository,
                        document_summary_repository=summary_repository,
                    ),
                    extraction_service=DocumentExtractionService(
                        document_repository=document_repository,
                        document_extraction_repository=extraction_repository,
                    ),
                )

                await comparison_service.fail_waiting_comparisons_for_document(
                    document_id=document_id,
                    error_message=(
                        "Required document summary generation failed: "
                        f"{error_message}"
                    ),
                )

                await session.commit()

            return
        # Commit PROCESSING before calling OpenAI.
        logger.info(
            "Commit PROCESSING before calling OpenAI."
        )

        await session.commit()

    # ==========================================================
    # Phase 2: Generate summary
    # No database session is held here.
    # ==========================================================

    try:

        content = await document_summarization_agent.summarize(
            chunks=chunks,
        )

        if not content or not content.strip():
            raise ValueError(
                "The summarization agent returned an empty summary."
            )

    except Exception as exc:
        logger.exception(
            "Summary generation failed. "
            "[document_id=%s, generation_id=%s]",
            document_id,
            generation_id,
        )

        async with AsyncSessionLocal() as session:
            summary_repository = DocumentSummaryRepository(session)

            updated = await summary_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message=str(exc)[:4000],
            )

            await session.commit()

            if not updated:
                logger.warning(
                    "Could not mark summary generation as FAILED because "
                    "it is no longer current. "
                    "[document_id=%s, generation_id=%s]",
                    document_id,
                    generation_id,
                )

        if updated and should_fail_prerequisite(exc, context):
            async with AsyncSessionLocal() as session:
                document_repository = DocumentRepository(session)

                comparison_service = DocumentComparisonOrchestrationService(
                    db=session,
                    summary_service=DocumentSummaryService(
                        document_repository=document_repository,
                        document_summary_repository=DocumentSummaryRepository(session),
                    ),
                    extraction_service=DocumentExtractionService(
                        document_repository=document_repository,
                        document_extraction_repository=DocumentExtractionRepository(session),
                    ),
                )

                failed_count = (
                    await comparison_service.fail_waiting_comparisons_for_document(
                        document_id=document_id,
                        error_message=(
                            "Required document summary generation failed: "
                            f"{str(exc)[:3500]}"
                        ),
                    )
                )

                await session.commit()

                logger.info(
                    "Marked comparisons as FAILED due to summary failure. "
                    "[document_id=%s, failed_count=%s]",
                    document_id,
                    failed_count,
                )

        raise

    # ==========================================================
    # Transaction 3: Persist completed summary
    # PROCESSING -> COMPLETED
    # Only updates if this generation is still current.
    # ==============================================================

    async with AsyncSessionLocal() as session:

        summary_repository = DocumentSummaryRepository(session)

        updated = await summary_repository.set_completed(
            document_id=document_id,
            generation_id=generation_id,
            content=content,
        )

        await session.commit()

        if not updated:
            logger.warning(
                "Generated summary is outdated. Skipping persistence. "
                "[document_id=%s, generation_id=%s]",
                document_id,
                generation_id,
            )
            return

    await coordinate_document_comparisons.kiq(
        document_id_str=str(document_id),
    )

    logger.info(
        "Successfully generated document summary. "
        "[document_id=%s, generation_id=%s]",
        document_id,
        generation_id,
    )

    return content
