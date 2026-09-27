import cohere

from core.settings import settings
from schemas.search_result import SearchResult
from services.reranker.base import Reranker


class CohereReranker(Reranker):

    def __init__(self, api_key: str) -> None:
        self.client = cohere.AsyncClientV2(api_key=api_key)

    async def rerank(
            self,
            query: str,
            results: list[SearchResult],
            top_k: int = 5,
    ) -> list[SearchResult]:

        if not results:
            return []

        documents = [
            result.content
            for result in results
        ]

        response = await self.client.rerank(
            model=settings.cohere_rerank_model,
            query=query,
            documents=documents,
            top_n=top_k,
        )

        reranked_results = []

        for item in response.results:
            result = results[item.index]

            result.rerank_score = item.relevance_score

            reranked_results.append(result)

        return reranked_results
