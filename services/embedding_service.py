from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from embeddings.embedding_provider import EmbeddingProvider
from ingestion.embedding_status import EmbeddingStatus
from repositories.document_chunk_repository import DocumentChunkRepository


class EmbeddingService:

    def __init__(self,
                 session: AsyncSession,
                 repository: DocumentChunkRepository,
                 embedding_provider: EmbeddingProvider):
        self.session = session
        self.repository = repository
        self.embedding_provider = embedding_provider

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
