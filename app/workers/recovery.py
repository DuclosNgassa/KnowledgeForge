from app.core.db.database import AsyncSessionLocal
from app.observability.logging import logger
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.workers.broker import broker
from app.workers.tasks import embed_document


@broker.task
async def recover_embedding_jobs():
    async with AsyncSessionLocal() as session:
        document_chunk_repository = DocumentChunkRepository(session)
        document_ids = await document_chunk_repository.find_documents_with_pending_chunks()

        for document_id in document_ids:
            await embed_document.kiq(str(document_id))

        logger.info(
            "Queued %d documents for embedding recovery",
            len(document_ids),
        )

        return len(document_ids)
