from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.embedding_status import EmbeddingStatus
from models import DocumentChunk


class DocumentChunkRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_all(self,
                       chunks: list[DocumentChunk]
                       ) -> list[DocumentChunk]:
        self.session.add_all(chunks)

        await self.session.flush()

        return chunks

    async def find_pending(self,
                           document_id: UUID | None = None,
                           limit: int = 100) -> list[DocumentChunk]:
        query = select(
            DocumentChunk
        ).where(
            DocumentChunk.embedding_status == EmbeddingStatus.PENDING
        ).order_by(
            DocumentChunk.created_at
        ).limit(limit)

        if document_id is not None:
            query = query.where(
                DocumentChunk.document_id == document_id
            )

        result = await self.session.execute(query)

        return list(result.scalars().all())
