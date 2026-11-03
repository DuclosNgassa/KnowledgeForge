from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentStatus, SummaryStatus


class DocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID | None = None
    status: DocumentStatus
    file_name: str
    title: str | None
    description: str | None
    document_type: str
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentSummaryResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    status: SummaryStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )
