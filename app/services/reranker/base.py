from abc import ABC, abstractmethod

from app.schemas.search_result import SearchResult


class Reranker(ABC):

    @abstractmethod
    async def rerank(
            self,
            query: str,
            results: list[SearchResult],
            top_k: int = 5,
            request_id: str | None = None,
    ) -> list[SearchResult]:
        pass
