from uuid import UUID

from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.observability.langfuse import langfuse

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.search_result import SearchResult


def _reciprocal_rank_fusion(
        result_lists,
        k: int = 60,
) -> list[SearchResult]:
    scores: dict[UUID, float] = {}
    items: dict[UUID, SearchResult] = {}

    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            chunk_id = item.chunk_id

            scores[chunk_id] = (
                    scores.get(chunk_id, 0.0)
                    + 1.0 / (k + rank)
            )

            items[chunk_id] = item

    ranked_ids = sorted(
        scores,
        key=scores.get,
        reverse=True,
    )

    return [
        items[chunk_id]
        for chunk_id in ranked_ids
    ]


class SearchService:

    def __init__(self,
                 document_chunk_repository: DocumentChunkRepository,
                 embedding_provider: EmbeddingProvider
                 ):
        self.embedding_provider = embedding_provider
        self.document_chunk_repository = document_chunk_repository

    async def do_similarity_search(self,
                                   query: str,
                                   user_id: UUID,
                                   limit: int = 5,
                                   ) -> list[SearchResult]:
        query_embeddings = await self.embedding_provider.embed_query(query)

        rows = await self.document_chunk_repository.do_similarity_search(query_embeddings, limit, user_id)

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

    async def do_keyword_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 5,
    ) -> list[SearchResult]:
        rows = await self.document_chunk_repository.do_keyword_search(
            query,
            user_id,
            limit,
        )

        return [
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

    async def do_hybrid_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 10,
            request_id: str | None = None,
    ):
        # 1. Semantic search
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="vector_search",
                input={
                    "query": query,
                    "limit": limit,
                },
        ) as observation:
            vector_results = await self.do_similarity_search(
                query=query,
                user_id=user_id,
                limit=20,
            )

            observation.update(
                output={
                    "result_count": len(vector_results),
                }
            )
            # print("Result of semantic search: ", vector_results)

        # 2. Keyword search
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="keyword_search",
                input={
                    "query": query,
                    "limit": limit,
                },
        ) as observation:
            keyword_results = await self.do_keyword_search(
                query=query,
                user_id=user_id,
                limit=20,
            )

            observation.update(
                output={
                    "result_count": len(keyword_results),
                }
            )
            print("\n")
            # print("Result of keyword search: ", vector_results)

            result_lists = [vector_results, keyword_results]

        # 3. Fuse results
        with langfuse.start_as_current_observation(
                as_type="span",
                name="rrf_fusion",
                input={
                    "vector_count": len(vector_results),
                    "keyword_count": len(keyword_results),
                },
        ) as observation:
            fused_results = _reciprocal_rank_fusion(
                result_lists=result_lists
            )
            print("\n")
            # print("Final fusion search: ", vector_results)
        observation.update(
            output={"result_count": len(fused_results)}
        )
        return fused_results[:limit]
