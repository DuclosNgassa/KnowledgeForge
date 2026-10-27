from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models.embedding_status import EmbeddingStatus
from app.models import DocumentChunk, Document
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

    async def find_pending_chunks(self,
                                  document_id: UUID | None = None,
                                  limit: int = 100) -> list[DocumentChunk]:
        query = select(
            DocumentChunk
        ).where(
            DocumentChunk.embedding_status.in_([
                EmbeddingStatus.PENDING,
                EmbeddingStatus.FAILED
            ])
        ).order_by(
            DocumentChunk.created_at
        ).limit(limit)

        if document_id is not None:
            query = query.where(
                DocumentChunk.document_id == document_id
            )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def find_documents_with_pending_chunks(self, ) -> list[UUID]:
        query = (
            select(DocumentChunk.document_id)
            .where(
                DocumentChunk.embedding_status.in_([
                    EmbeddingStatus.PENDING,
                    EmbeddingStatus.FAILED
                ])
            )
            .where(DocumentChunk.document_id.is_not(None))
            .distinct()
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def do_similarity_search(
            self,
            query_embedding,
            limit: int,
            user_id: UUID,
            knowledge_base_ids: list[UUID] | None = None,
    ):
        if knowledge_base_ids is not None and not knowledge_base_ids:
            return []

        distance = DocumentChunk.embedding.cosine_distance(query_embedding)

        stmt = (
            select(DocumentChunk, distance.label("distance"))
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .options(selectinload(DocumentChunk.document))
            .where(
                Document.user_id == user_id,
                DocumentChunk.embedding.is_not(None),
            )
        )

        if knowledge_base_ids is not None:
            stmt = stmt.where(
                Document.knowledge_base_id.in_(knowledge_base_ids)
            )

        stmt = stmt.order_by(distance).limit(limit)

        result = await self.session.execute(stmt)
        return result.all()

    async def do_keyword_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 20,
            knowledge_base_ids: list[UUID] | None = None,
    ):
        if knowledge_base_ids is not None and not knowledge_base_ids:
            return []

        ts_query = func.plainto_tsquery("simple", query)

        keyword_score = func.ts_rank(
            DocumentChunk.search_vector,
            ts_query,
        )

        stmt = (
            select(
                DocumentChunk,
                keyword_score.label("keyword_score"),
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .options(selectinload(DocumentChunk.document))
            .where(
                Document.user_id == user_id,
                DocumentChunk.search_vector.op("@@")(ts_query),
            )
        )

        if knowledge_base_ids is not None:
            stmt = stmt.where(
                Document.knowledge_base_id.in_(knowledge_base_ids)
            )

        stmt = stmt.order_by(keyword_score.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.all()

    async def find_by_ids(self, chunk_ids: list[UUID]) -> list[DocumentChunk]:
        query = select(
            DocumentChunk
        ).where(DocumentChunk.id.in_(chunk_ids))

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def mark_failed(self, chunk_ids: list[UUID]) -> None:
        await self.session.execute(
            update(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
            .values(embedding_status=EmbeddingStatus.FAILED)
        )
