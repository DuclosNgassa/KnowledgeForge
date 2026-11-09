from datetime import date as Date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import ExtractionStatus


class ExtractedEntity(BaseModel):
    name: str = Field(
        description="Name of the extracted entity."
    )

    entity_type: str = Field(
        description="Entity type, e.g. PERSON, ORGANIZATION, PRODUCT, TECHNOLOGY."
    )

    description: str | None = Field(
        default=None,
        description="Brief explanation of the entity in the document."
    )


class ExtractedDate(BaseModel):
    date: Date = Field(
        description="The extracted date in ISO format."
    )
    description: str = Field(
        description="What this date refers to."
    )


class DocumentExtractionResult(BaseModel):
    document_category: str = Field(
        description="The primary category of the document."
    )

    key_topics: list[str] = Field(
        default_factory=list,
        description="The main topics discussed in the document."
    )

    named_entities: list[ExtractedEntity] = Field(
        default_factory=list,
        description="Important people, organizations, products and other named entities."
    )

    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies, frameworks, programming languages and tools mentioned."
    )

    important_dates: list[ExtractedDate] = Field(
        default_factory=list,
        description="Important dates and their context."
    )

    key_findings: list[str] = Field(
        default_factory=list,
        description="Important facts, conclusions, decisions and findings."
    )


class DocumentExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    extraction_data: dict | None
    status: ExtractionStatus
    generation_id: UUID | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
