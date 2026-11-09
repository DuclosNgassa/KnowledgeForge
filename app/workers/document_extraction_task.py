from uuid import UUID

from app.agents.agent_factory import create_document_extraction_agent
from app.core.db.database import AsyncSessionLocal
from app.models.document import DocumentStatus
from app.observability.logging import logger
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from app.workers.broker import broker

document_extraction_agent = create_document_extraction_agent()


@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def extract_document(
        document_id_str: str,
        generation_id_str: str,
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

    async with AsyncSessionLocal() as db:
        document_repository = DocumentRepository(db)
        chunk_repository = DocumentChunkRepository(db)
        extraction_repository = DocumentExtractionRepository(db)

        document = await document_repository.find_document_by_id_for_processing(
            document_id=document_id,
        )

        if document is None:
            logger.warning(
                "Document not found for extraction | document_id=%s",
                document_id,
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

        if document.status != DocumentStatus.READY:
            await extraction_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message="Document is not ready for extraction.",
            )
            await db.commit()

            logger.warning(
                "Document is not ready for extraction | document_id=%s",
                document_id,
            )
            return

        chunks = await chunk_repository.find_chunks_by_document_id(
            document_id=document_id,
        )

        if not chunks:
            await extraction_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message="Document has no chunks to extract.",
            )
            await db.commit()

            logger.warning(
                "Document has no chunks | document_id=%s",
                document_id,
            )
            return

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

        await db.commit()

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

        async with AsyncSessionLocal() as db:
            extraction_repository = DocumentExtractionRepository(db)

            await extraction_repository.set_failed(
                document_id=document_id,
                generation_id=generation_id,
                error_message=str(exc)[:2000],
            )

            await db.commit()

        # Re-raise so Taskiq retry middleware can handle the failure.
        raise

    # ---------------------------------------------------------
    # Phase 3b: Persist successful extraction
    # ---------------------------------------------------------

    async with AsyncSessionLocal() as db:
        extraction_repository = DocumentExtractionRepository(db)

        updated = await extraction_repository.set_completed(
            document_id=document_id,
            generation_id=generation_id,
            extraction_data=extraction_data,
        )

        await db.commit()

        if not updated:
            logger.info(
                "Extraction result discarded because generation is outdated | "
                "document_id=%s | generation_id=%s",
                document_id,
                generation_id,
            )
            return

    logger.info(
        "Document extraction completed | document_id=%s | generation_id=%s",
        document_id,
        generation_id,
    )
