from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.ingestion.models.document_status import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID | None = None
    status: DocumentStatus
    file_name: str
    document_type: str
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )
