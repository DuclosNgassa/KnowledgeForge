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
    filename: str
    content: str
    page_number: int | None = None


class WebSource(BaseModel):
    title: str
    url: str
