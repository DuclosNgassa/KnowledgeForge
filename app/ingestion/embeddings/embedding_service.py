from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.models.enums import EmbeddingStatus
from app.observability.logging import logger
from app.repositories.document_chunk_repository import DocumentChunkRepository


class EmbeddingService:

    def __init__(self,
                 session: AsyncSession,
                 repository: DocumentChunkRepository,
                 embedding_provider: EmbeddingProvider | None):
        self.session = session
        self.repository = repository
        self.embedding_provider = embedding_provider

    # TODO remove later
    async def process_pending_chunks(self,
                                     document_id: UUID | None = None,
                                     limit: int = 100) -> int:
        chunks = await self.repository.find_pending_chunks(document_id=document_id, limit=limit)

        if not chunks:
            return 0
        try:
            # PENDING → PROCESSING
            for chunk in chunks:
                chunk.embedding_status = (
                    EmbeddingStatus.PROCESSING
                )
            await self.session.flush()

            # Generate embeddings
            texts = [
                chunk.content
                for chunk in chunks
            ]

            try:
                embeddings = await self.embedding_provider.embed_documents(texts)
            except Exception as e:
                logger.exception(
                    "Embedding failed for document %s. [exception: %s]",
                    document_id, e,
                )
                raise

            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Number of embeddings does not match the number of chunks. [len_embedding={len(embeddings)}, len_chunks={len(chunks)}]"
                )

            # Save embeddings
            for chunk, embedding in zip(
                    chunks,
                    embeddings
            ):
                chunk.embedding = embedding
                chunk.embedding_status = EmbeddingStatus.COMPLETED

            # await self.embedding_repository.save_all(chunks)
            await self.session.commit()

            return len(chunks)

        except Exception:
            await self.session.rollback()
            raise

    async def claim_pending_chunks(
            self,
            document_id: UUID | None = None,
            limit: int = 100) -> list[UUID]:
        chunks = await self.repository.find_pending_chunks(document_id=document_id, limit=limit)

        if not chunks:
            return []

        chunk_ids = []
        for chunk in chunks:
            chunk.embedding_status = EmbeddingStatus.PROCESSING
            chunk_ids.append(chunk.id)

        await self.session.commit()

        return chunk_ids

    async def embed_chunks(
            self,
            chunk_ids: list[UUID],
    ) -> int:

        chunks = await self.repository.find_by_ids(chunk_ids)

        if not chunks:
            logger.info(
                "No chunks found. They may have been deleted: %s",
                chunk_ids,
            )
            return 0

        if len(chunks) != len(chunk_ids):
            existing_ids = {chunk.id for chunk in chunks}
            missing_ids = set(chunk_ids) - existing_ids

            logger.info(
                "Some chunks no longer exist, possibly because their document "
                "was deleted. Skipping missing chunks: %s",
                missing_ids,
            )

        texts = [chunk.content for chunk in chunks]

        try:
            embeddings = await self.embedding_provider.embed_documents(texts)

            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Expected {len(chunks)} embeddings, got {len(embeddings)}"
                )

            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                chunk.embedding_status = EmbeddingStatus.COMPLETED

            await self.session.commit()

            return len(chunks)

        except Exception:
            logger.exception(
                "Embedding failed for chunks %s",
                [chunk.id for chunk in chunks],
            )

            await self.repository.mark_failed(
                [chunk.id for chunk in chunks]
            )
            await self.session.commit()
            raise