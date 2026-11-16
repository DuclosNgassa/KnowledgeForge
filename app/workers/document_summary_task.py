import asyncio
from uuid import UUID

from taskiq import Context, TaskiqDepends

from app.core.db.database import AsyncSessionLocal
from app.observability.logging import logger
from app.workers.broker import broker

from app.repositories.document_repository import DocumentRepository
from app.repositories.document_summary_repository import (
    DocumentSummaryRepository,
)
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)

from app.models.document import DocumentStatus

from app.agents.agent_factory import (
    create_document_summarization_agent,
)

# ==============================================================
# Summarization agent
# ==============================================================

document_summarization_agent = (
    create_document_summarization_agent()
)

# ==============================================================
# Shared summarization concurrency control
# ==============================================================

_summarization_semaphore = asyncio.Semaphore(1)


async def _run_summary_with_semaphore(
        document_id_str: str,
        generation_id_str: str,
):
    """
    Execute one summary generation at a time
    within this worker process.
    """

    async with _summarization_semaphore:
        return await _generate_document_summary(
            document_id_str=document_id_str,
            generation_id_str=generation_id_str,
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
    )


# ==============================================================
# Summary generation implementation
# ==============================================================

async def _generate_document_summary(
        document_id_str: str,
        generation_id_str: str,
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
            error_message = "Document has no chunks to summarize."

            logger.error(
                "%s [document_id=%s, generation_id=%s]",
                error_message,
                document_id,
                generation_id,
            )

            await summary_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message=error_message,
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

        # ======================================================
        # Transaction 2: Mark current generation as FAILED
        # Only updates if this generation is still current.
        # ======================================================

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
                    "Could not mark generation as FAILED because "
                    "it is no longer current. "
                    "[document_id=%s, generation_id=%s]",
                    document_id,
                    generation_id,
                )

        # Re-raise so Taskiq can apply its retry policy.
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

    logger.info(
        "Successfully generated document summary. "
        "[document_id=%s, generation_id=%s]",
        document_id,
        generation_id,
    )

    return content
