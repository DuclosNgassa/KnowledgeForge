from dataclasses import dataclass
from uuid import UUID


@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    content: str
    source: str
    page_number: int
    score: float
