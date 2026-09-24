from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from embeddings.embedding_provider import EmbeddingProvider
from models import DocumentChunk
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from schemas.search_result import SearchResult


class SimilaritySearchService:

    def __init__(self,
                 session: AsyncSession,
                 embedding_provider: EmbeddingProvider
                 ):
        self.session = session
        self.embedding_provider = embedding_provider

    async def search(self,
                     query: str,
                     user_id: UUID,
                     limit: int = 5,
                     ) -> list[SearchResult]:
        query_embeddings = await self.embedding_provider.embed_query(query)

        distance = (
            DocumentChunk.embedding.cosine_distance(
                query_embeddings
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

        rows = result.all()

        return [
            SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                source=chunk.document.source,
                file_name=chunk.document.file_name,
                page_number=chunk.page_number,
                score=1 - distance_value,
            )
            for chunk, distance_value in rows
        ]
