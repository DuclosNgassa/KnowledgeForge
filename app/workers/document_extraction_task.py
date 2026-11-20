import asyncio
from uuid import UUID

from taskiq import Context, TaskiqDepends

from app.agents.agent_factory import create_document_extraction_agent
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

document_extraction_agent = create_document_extraction_agent()

_extraction_semaphore = asyncio.Semaphore(1)


async def _run_extraction_with_semaphore(
        document_id_str: str,
        generation_id_str: str,
        context: Context,
) -> None:
    async with _extraction_semaphore:
        await _extract_document(
            document_id_str=document_id_str,
            generation_id_str=generation_id_str,
            context=context
        )


@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def extract_document(
        document_id_str: str,
        generation_id_str: str,
        context: Context = TaskiqDepends(),
) -> None:
    await _run_extraction_with_semaphore(
        document_id_str=document_id_str,
        generation_id_str=generation_id_str,
        context=context,
    )


async def _extract_document(
        document_id_str: str,
        generation_id_str: str,
        context: Context,
) -> None:
    """
    Extract or re-extract info from a document asynchronously.

    The generation_id ensures that an outdated worker cannot
    overwrite a newer extraction.
    """
    document_id = UUID(document_id_str)
    generation_id = UUID(generation_id_str)

    logger.info(
        "Starting document extraction | document_id=%s | generation_id=%s",
        document_id,
        generation_id,
    )

    # ---------------------------------------------------------
    # Phase 1: Claim extraction and load document chunks
    # ---------------------------------------------------------

    async with AsyncSessionLocal() as session:
        document_repository = DocumentRepository(session)
        summary_repository = DocumentSummaryRepository(session)
        chunk_repository = DocumentChunkRepository(session)
        extraction_repository = DocumentExtractionRepository(session)

        document = await document_repository.find_document_by_id_for_processing(
            document_id=document_id,
        )

        if document is None:
            logger.warning(
                "Document does not exist. "
                "Skipping structured extraction generation. "
                "[document_id=%s]",
                document_id,
            )
            return

        if document.status != DocumentStatus.READY:
            logger.error(
                "Document is not ready for structured extraction. "
                "[document_id=%s, status=%s]",
                document_id,
                document.status,
            )
            return

        extraction = await extraction_repository.claim_for_processing(
            document_id=document_id,
            generation_id=generation_id,
        )

        if extraction is None:
            logger.info(
                "Extraction already claimed or generation is outdated | "
                "document_id=%s | generation_id=%s",
                document_id,
                generation_id,
            )
            return

        chunks = await chunk_repository.find_chunks_by_document_id(
            document_id=document_id,
        )

        if not chunks:
            error_message = f"Document has no chunks to extract | document_id={document_id} | generation_id={generation_id}"

            logger.error(error_message)

            updated = await extraction_repository.set_failed(
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
                        "Required structured extraction generation failed: "
                        f"{error_message}"
                    ),
                )

                await session.commit()

            return

        # Commit PROCESSING before calling OpenAI.
        logger.info(
            "Commit PROCESSING before calling OpenAI."
        )
        # Keep only the data needed by the agent.
        # This avoids depending on ORM objects after the session closes.
        chunks_data = [
            {
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content,
            }
            for chunk in chunks
        ]

        await session.commit()

    # ---------------------------------------------------------
    # Phase 2: Run extraction without a database session
    # ---------------------------------------------------------

    try:
        result = await document_extraction_agent.extract(chunks_data)

        extraction_data = result.model_dump(mode="json")

    except Exception as exc:
        logger.exception(
            "Document extraction failed | document_id=%s | generation_id=%s",
            document_id,
            generation_id,
        )

        # -----------------------------------------------------
        # Phase 3a: Persist failure
        # -----------------------------------------------------

        async with AsyncSessionLocal() as session:
            extraction_repository = DocumentExtractionRepository(session)

            updated = await extraction_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message=str(exc)[:2000],
            )

            await session.commit()

            if not updated:
                logger.warning(
                    "Could not mark structured extraction generation as FAILED because "
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
                            "Required structured extraction generation failed: "
                            f"{str(exc)[:3500]}"
                        ),
                    )
                )

                await session.commit()

                logger.info(
                    "Marked comparisons as FAILED due to structured extraction failure. "
                    "[document_id=%s, failed_count=%s]",
                    document_id,
                    failed_count,
                )

        # Re-raise so Taskiq retry middleware can handle the failure.
        raise

    # ---------------------------------------------------------
    # Phase 3b: Persist successful extraction
    # ---------------------------------------------------------

    async with AsyncSessionLocal() as session:
        extraction_repository = DocumentExtractionRepository(session)

        updated = await extraction_repository.set_completed(
            document_id=document_id,
            generation_id=generation_id,
            extraction_data=extraction_data,
        )

        await session.commit()

        if not updated:
            logger.info(
                "Extraction result discarded because generation is outdated | "
                "document_id=%s | generation_id=%s",
                document_id,
                generation_id,
            )
            return

    await coordinate_document_comparisons.kiq(
        document_id_str=str(document_id),
    )

    logger.info(
        "Document extraction completed | document_id=%s | generation_id=%s",
        document_id,
        generation_id,
    )
