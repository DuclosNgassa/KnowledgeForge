from uuid import UUID

from app.core.db.database import AsyncSessionLocal
from app.core.settings import settings
from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.ingestion.embeddings.embedding_provider_type import EmbeddingProviderType
from app.ingestion.embeddings.embedding_service import EmbeddingService
from app.ingestion.embeddings.google_provider import GoogleEmbeddingProvider
from app.ingestion.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.observability.logging import logger
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository

from app.workers.broker import broker


@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def embed_document(
        document_id_str: str | None = None,
):
    logger.debug(f"Starting embedding for document {document_id_str}")
    print(f"Starting embedding for document {document_id_str}")

    if document_id_str is None:
        logger.warning(f"No document id provided for {document_id_str}")
        return 0

    document_id = UUID(document_id_str)

    total_embedded = 0

    while True:
        # ==========================================
        # Transaction 1: Claim chunks
        # PENDING → PROCESSING
        # ==========================================
        async with AsyncSessionLocal() as session:
            repository = DocumentChunkRepository(session)

            embedding_service = EmbeddingService(
                session=session,
                repository=repository,
                embedding_provider=None,
            )

            chunk_ids = await embedding_service.claim_pending_chunks(
                document_id=document_id,
                limit=100
            )

        # No more chunks
        if not chunk_ids:
            logger.warning(f"No more chunks to embed for document {document_id}")
            break

        # ==========================================
        # Transaction 2: Generate embeddings
        # PROCESSING → COMPLETED
        # ==========================================
        async with AsyncSessionLocal() as session:
            repository = DocumentChunkRepository(session)
            embedding_provider = get_embedding_provider(provider=EmbeddingProviderType.OPENAI)

            embedding_service = EmbeddingService(
                session=session,
                repository=repository,
                embedding_provider=embedding_provider,
            )

            result = await embedding_service.embed_chunks(chunk_ids)
            total_embedded += result

        logger.debug(
            f"Embedded {result} chunks for document {document_id}"
        )

    # All chunks are now embedded
    async with AsyncSessionLocal() as session:
        document_repository = DocumentRepository(session)
        print("Finished embedding for document {}".format(document_id_str))
        await document_repository.set_document_to_ready(document_id=document_id)

        await session.commit()

    logger.info(
        f"Finished embedding document {document_id}: "
        f"{total_embedded} chunks"
    )

    return total_embedded

def get_google_embedding_provider(model: str = settings.google_embedding_model) -> EmbeddingProvider:
    return GoogleEmbeddingProvider(
        model=model,
    )


def get_openai_embedding_provider(model: str = settings.openai_embedding_model) -> EmbeddingProvider:
    return OpenAIEmbeddingProvider(
        model=model,
    )


def get_embedding_provider(provider: EmbeddingProviderType) -> EmbeddingProvider:
    if provider == EmbeddingProviderType.GEMINI:
        return get_google_embedding_provider()
    elif provider == EmbeddingProviderType.OPENAI:
        return get_openai_embedding_provider()
    raise ValueError(f"Unknown embedding provider {provider}")
