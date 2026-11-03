import logging
from uuid import UUID

from app.agents.agent_factory import (
    create_document_summarization_agent,
)
from app.core.db.database import AsyncSessionLocal
from app.models.enums import DocumentStatus, SummaryStatus
from app.observability.logging import logger
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_summary_repository import (
    DocumentSummaryRepository,
)
from app.workers.broker import broker

# Reuse the agent within this worker process.
document_summarization_agent = (
    create_document_summarization_agent()
)


@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def generate_document_summary(
        document_id_str: str,
):
    """
    uv run taskiq worker --app-dir . --workers 1 app.workers.worker:broker app.workers.document_summary_task.generate_document_summary
    """
    document_id = UUID(document_id_str)

    logger.info(
        "Starting summary generation for document %s",
        document_id,
    )

    # ==========================================
    # Transaction 1: Validate and claim summary
    # PENDING / FAILED -> PROCESSING
    # ==========================================

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
                f"Document does not exist. Skipping summary. [document_id={document_id}]",
            )
            return

        if document.status != DocumentStatus.READY:
            raise ValueError(
                f"Document is not ready for summarization. [document_id={document_id}]"
            )

        summary = await summary_repository.claim_for_processing(
            document_id=document_id,
        )

        if summary is None:
            logger.info(
                f"Summary for document %s is already processed or completed. Skipping. [document_id={document_id}]",
            )
            return

        chunks = await chunk_repository.find_chunks_by_document_id(
            document_id=document_id,
        )

        if not chunks:
            raise ValueError(
                f"Document has no chunks to summarize. [document_id={document_id}]"
            )

        # Commit the PROCESSING status before calling OpenAI.
        await session.commit()

    # ==========================================
    # Phase 2: Generate summary
    # No database session is held here.
    # ==========================================

    try:
        content = await document_summarization_agent.summarize(
            chunks=chunks,
        )

        if not content.strip():
            raise ValueError(
                "The summarization agent returned an empty summary"
            )

    except Exception as exc:
        logger.exception(
            "Summary generation failed for document %s",
            document_id,
        )

        # ==========================================
        # Transaction 3: Mark summary as FAILED
        # ==========================================

        async with AsyncSessionLocal() as session:
            summary_repository = DocumentSummaryRepository(session)

            summary = await summary_repository.find_by_document_id(
                document_id=document_id,
            )

            if summary is not None:
                await summary_repository.set_failed(
                    document_summary=summary,
                    error_message=str(exc)[:4000],
                )

            await session.commit()

        raise

    # ==========================================
    # Transaction 4: Persist completed summary
    # PROCESSING -> COMPLETED
    # ==========================================

    async with AsyncSessionLocal() as session:
        summary_repository = DocumentSummaryRepository(session)

        summary = await summary_repository.find_by_document_id(
            document_id=document_id,
        )

        if summary is None:
            raise ValueError(
                f"Summary record for document {document_id} not found"
            )

        if summary.status != SummaryStatus.PROCESSING:
            logger.warning(
                "Summary status changed while generating document %s. "
                "Skipping persistence.",
                document_id,
            )
            return

        await summary_repository.set_completed(
            document_summary=summary,
            content=content,
        )

        await session.commit()

    logger.info(
        "Successfully generated summary for document %s",
        document_id,
    )

    return content
