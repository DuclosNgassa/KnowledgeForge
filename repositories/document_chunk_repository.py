from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.embedding_status import EmbeddingStatus
from models import DocumentChunk, Document
from sqlalchemy.orm import selectinload


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

    async def do_similarity_search(
            self,
            query_embedding,
            limit: int,
            user_id: UUID,
    ):
        distance = (
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            )
        )

        result = await self.session.execute(
            select(DocumentChunk, distance.label("distance"))
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.embedding.is_not(None))
            .where(DocumentChunk.document.has(user_id=user_id))
            .order_by(distance)
            .limit(limit)
        )
        return result.all()

    async def do_keyword_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 20
    ):
        ts_query = func.plainto_tsquery("simple", query)

        stmt = (
            select(
                DocumentChunk,
                func.ts_rank(
                    DocumentChunk.search_vector,
                    ts_query,
                ).label("keyword_score"),
            )
            .options(selectinload(DocumentChunk.document))
            .join(
                Document,
                Document.id == DocumentChunk.document_id
            ).where(
                Document.user_id == user_id,
                DocumentChunk.search_vector.op("@@")(ts_query),
            ).order_by(
                func.ts_rank(
                    DocumentChunk.search_vector,
                    ts_query,
                ).desc()
            ).limit(limit)
        )

        result = await self.session.execute(stmt)

        return result.all()
