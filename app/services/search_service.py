from uuid import UUID

from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.observability.langfuse import langfuse

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.search_result import SearchResult


def _reciprocal_rank_fusion(
        result_lists,
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

                items[chunk_id] = item

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

    async def do_similarity_search(self,
                                   query: str,
                                   user_id: UUID,
                                   limit: int = 5,
                                   ) -> list[SearchResult]:
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="similarity_search",
                input={
                    "query": query,
                    "limit": limit,
                },
        ) as observation:
            query_embeddings = await self.embedding_provider.embed_query(query)

            rows = await self.document_chunk_repository.do_similarity_search(query_embeddings, limit, user_id)

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
    ) -> list[SearchResult]:
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="keyword_search",
                input={
                    "query": query,
                    "limit": limit,
                },
        ) as observation:
            rows = await self.document_chunk_repository.do_keyword_search(
                query,
                user_id,
                limit,
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
                output={
                    "result_count": len(results),
                }
            )

            return results

    async def do_hybrid_search(
            self,
            query: str,
            user_id: UUID,
            limit: int = 10,
            request_id: str | None = None,
    ):
        # 1. Semantic search
        with langfuse.start_as_current_observation(
                as_type="span",
                name="hybrid_search",
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

            # print("Result of semantic search: ", vector_results)

            # 2. Keyword search
            keyword_results = await self.do_keyword_search(
                query=query,
                user_id=user_id,
                limit=20,
            )

            # print("Result of keyword search: ", vector_results)

            result_lists = [vector_results, keyword_results]

            # 3. Fuse results
            fused_results = _reciprocal_rank_fusion(
                result_lists=result_lists
            )
            print("\n")
            # print("Final fusion search: ", vector_results)

            results_hybrid_search = fused_results[:limit]

            observation.update(
                output={
                    "result_count": len(results_hybrid_search)
                }
            )

            return results_hybrid_search
