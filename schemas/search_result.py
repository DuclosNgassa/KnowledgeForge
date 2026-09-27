from dataclasses import dataclass
from uuid import UUID


@dataclass
class BaseSearchResult:
    content: str
    rerank_score: float | None = None

# RAG layer's data structure.
@dataclass(kw_only=True)
class SearchResult(BaseSearchResult):
    chunk_id: UUID
    document_id: UUID
    source: str
    file_name: str
    page_number: int
    score: float


# RAG layer's data structure.
@dataclass(kw_only=True)
class WebSearchResult(BaseSearchResult):
    title: str
    url: str
