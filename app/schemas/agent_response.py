from uuid import UUID

from pydantic import BaseModel, Field


# API/LLM layer's data structure.
class AgentResponse(BaseModel):
    answer: str
    sources: list[SourceReference]  # = Field(default_factory=list)
    web_sources: list[WebSource]


class SourceReference(BaseModel):
    chunk_id: UUID | None = None
    document_id: UUID
    page_number: int | None = None
    filename: str
    content: str


class WebSource(BaseModel):
    title: str
    url: str
