import asyncio
from uuid import UUID

from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.observability.langfuse import langfuse

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.search_result import SearchResult


def _reciprocal_rank_fusion(
        result_lists: list[list[SearchResult]],
        k: int = 60,
) -> list[SearchResult]:
    with langfuse.start_as_current_observation(
            as_type="span",
            name="rrf_fusion",
    ) as observation:
        scores: dict[UUID, float] = {}
        items: dict[UUID, SearchResult] = {}

        for results in result_lists:
            for rank, item in enumerate(results, start=1):
                chunk_id = item.chunk_id

                scores[chunk_id] = (
                        scores.get(chunk_id, 0.0)
                        + 1.0 / (k + rank)
                )

                items.setdefault(chunk_id, item)

        ranked_ids = sorted(
            scores,
            key=scores.get,
            reverse=True,
        )

        ranked_results = [
            items[chunk_id]
            for chunk_id in ranked_ids
        ]

        observation.update(
            output={
                "result_count": len(ranked_results),
            }
        )
        return ranked_results


class SearchService:

    def __init__(self,
                 document_chunk_repository: DocumentChunkRepository,
                 embedding_provider: EmbeddingProvider
                 ):
        self.embedding_provider = embedding_provider
        self.document_chunk_repository = document_chunk_repository

    async def do_similarity_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 5,
            knowledge_base_ids: list[UUID] | None = None,
    ) -> list[SearchResult]:
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="similarity_search",
                input={
                    "query": query,
                    "limit": limit,
                    "knowledge_base_ids": (
                            [str(kb_id) for kb_id in knowledge_base_ids]
                            if knowledge_base_ids is not None
                            else None
                    ),
                },
        ) as observation:
            query_embeddings = await self.embedding_provider.embed_query(query)

            rows = await self.document_chunk_repository.do_similarity_search(query_embeddings,
                                                                             limit,
                                                                             user_id,
                                                                             knowledge_base_ids)

            results = [
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

            observation.update(
                output={
                    "result_count": len(results),
                }
            )

            return results

    async def do_keyword_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 5,
            knowledge_base_ids: list[UUID] | None = None,
    ) -> list[SearchResult]:
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="keyword_search",
                input={
                    "query": query,
                    "limit": limit,
                    "knowledge_base_ids": (
                            [str(kb_id) for kb_id in knowledge_base_ids]
                            if knowledge_base_ids is not None
                            else None
                    ),
                },
        ) as observation:
            rows = await self.document_chunk_repository.do_keyword_search(
                query=query,
                user_id=user_id,
                limit=limit,
                knowledge_base_ids=knowledge_base_ids,
            )

            results = [
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    source=chunk.document.source,
                    file_name=chunk.document.file_name,
                    page_number=chunk.page_number,
                    score=keyword_score,
                )
                for chunk, keyword_score in rows
            ]

            observation.update(
                output={"result_count": len(results)}
            )

            return results

    async def do_multi_query_hybrid_search(
            self,
            queries: list[str],
            user_id: UUID,
            limit: int = 5,
            request_id: str | None = None,
            knowledge_base_ids: list[UUID] | None = None,
    ) -> list[SearchResult]:
        """Retrieve across multiple queries and fuse their rankings."""

        unique_queries = list(
            dict.fromkeys(
                query.strip()
                for query in queries
                if query and query.strip()
            )
        )

        if not unique_queries:
            return []

        if knowledge_base_ids is not None and not knowledge_base_ids:
            return []

        result_lists = await asyncio.gather(
            *[
                self.do_hybrid_search(
                    query=query,
                    user_id=user_id,
                    limit=limit,
                    request_id=request_id,
                    knowledge_base_ids=knowledge_base_ids
                )
                for query in unique_queries
            ]
        )

        fused_results = _reciprocal_rank_fusion(
            result_lists=result_lists,
        )

        return fused_results[:limit]

    async def do_hybrid_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 20,
            request_id: str | None = None,
            knowledge_base_ids: list[UUID] | None = None,
    ) -> list[SearchResult]:
        # An explicit empty scope must never broaden the search.
        if knowledge_base_ids is not None and not knowledge_base_ids:
            return []

        with langfuse.start_as_current_observation(
                as_type="span",
                name="hybrid_search",
                input={
                    "query": query,
                    "limit": limit,
                    "knowledge_base_ids": (
                            [str(kb_id) for kb_id in knowledge_base_ids]
                            if knowledge_base_ids is not None
                            else None
                    ),
                },
        ) as observation:
            # 1. Semantic search
            vector_results = await self.do_similarity_search(
                query=query,
                user_id=user_id,
                limit=limit,
                knowledge_base_ids=knowledge_base_ids,
            )

            # 2. Keyword search
            keyword_results = await self.do_keyword_search(
                query=query,
                user_id=user_id,
                limit=limit,
                knowledge_base_ids=knowledge_base_ids,
            )

            # 3. Fuse the already-scoped results
            fused_results = _reciprocal_rank_fusion(
                result_lists=[vector_results, keyword_results]
            )

            results = fused_results[:limit]

            observation.update(
                output={"result_count": len(results)}
            )

            return results
