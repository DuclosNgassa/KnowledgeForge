from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.ingestion.models.embedding_status import EmbeddingStatus
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
        chunks = await self.repository.find_pending(document_id=document_id, limit=limit)

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

            embeddings = await self.embedding_provider.embed_documents(texts)

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
        chunks = await self.repository.find_pending(document_id=document_id, limit=limit)

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
            chunk_ids: list[UUID], ) -> int:

        chunks = await self.repository.find_by_ids(chunk_ids)
        if len(chunks) != len(chunk_ids):
            raise ValueError(
                f"Expected {len(chunk_ids)} chunks, but got {len(chunks)}"
            )

        if not chunks:
            return 0

        texts = [chunk.content for chunk in chunks]
        try:
            embeddings = await self.embedding_provider.embed_documents(texts)
            if len(embeddings) != len(chunk_ids):
                raise ValueError(
                    f"Expected {len(chunks)} embeddings, but got {len(embeddings)}"
                )

            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                chunk.embedding_status = EmbeddingStatus.COMPLETED

            await self.session.commit()

            return len(chunks)

        except Exception:
            await self.repository.mark_failed(chunk_ids)
            await self.session.commit()
            raise
