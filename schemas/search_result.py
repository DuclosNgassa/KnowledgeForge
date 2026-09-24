from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel


# RAG layer's data structure.
@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    content: str
    source: str
    file_name: str
    page_number: int
    score: float


@dataclass
class WebSearchResult:
    title: str
    url: str
    content: str
