from uuid import UUID

from taskiq import Context, TaskiqDepends

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
from app.workers.retry import should_fail_prerequisite
from app.workers.broker import broker
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_summary_repository import DocumentSummaryRepository
from app.repositories.document_extraction_repository import DocumentExtractionRepository

from app.services.document_summary_service import DocumentSummaryService
from app.services.document_extraction_service import DocumentExtractionService
from app.services.document_comparison_orchestration_service import (
    DocumentComparisonOrchestrationService,
)

@broker.task(
    retry_on_error=True,
    max_retries=3
)
async def embed_document(
        document_id_str: str | None = None,
        context: Context = TaskiqDepends(),
):
    logger.debug(f"Starting embedding for document {document_id_str}")

    if document_id_str is None:
        logger.warning("No document id provided")
        return 0

    document_id = UUID(document_id_str)
    total_embedded = 0

    try:
        while True:
            # Transaction 1: Claim chunks
            async with AsyncSessionLocal() as session:
                repository = DocumentChunkRepository(session)

                embedding_service = EmbeddingService(
                    session=session,
                    repository=repository,
                    embedding_provider=None,
                )

                chunk_ids = await embedding_service.claim_pending_chunks(
                    document_id=document_id,
                    limit=100,
                )

            if not chunk_ids:
                logger.warning(
                    f"No more chunks to embed for document {document_id}"
                )
                break

            # Transaction 2: Generate embeddings
            async with AsyncSessionLocal() as session:
                repository = DocumentChunkRepository(session)
                embedding_provider = get_embedding_provider(
                    provider=EmbeddingProviderType.OPENAI
                )

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

            updated = await document_repository.set_document_to_ready(
                document_id=document_id
            )

            if updated:
                await session.commit()
            else:
                await session.rollback()
                logger.warning(
                    f"Document {document_id} was not marked READY "
                    "because some chunks are not COMPLETED"
                )

        logger.info(
            f"Finished embedding document {document_id}: "
            f"{total_embedded} chunks"
        )

        return total_embedded
    except Exception as exc:
        if should_fail_prerequisite(exc, context):
            error_message = f"Document embedding failed: {str(exc)}"

            async with AsyncSessionLocal() as session:
                document_repository = DocumentRepository(session)
                summary_repository = DocumentSummaryRepository(session)
                extraction_repository = DocumentExtractionRepository(session)

                updated = await document_repository.set_document_to_embedding_failed(
                    document_id=document_id,
                )

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
                        error_message=error_message,
                    )

                    await session.commit()

                    logger.error(
                        "Document %s marked EMBEDDING_FAILED. "
                        "Waiting comparisons have been failed.",
                        document_id,
                    )

        raise


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
