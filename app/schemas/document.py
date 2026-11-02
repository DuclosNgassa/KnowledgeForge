from uuid import UUID

from pydantic import BaseModel, HttpUrl, ConfigDict, Field, model_validator


class DocumentUrlRequest(BaseModel):
    url: HttpUrl
    knowledge_base_id: UUID


class UpdateDocumentKnowledgeBaseRequest(BaseModel):
    knowledge_base_id: UUID | None


class UpdateDocumentMetadataRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.model_fields_set.intersection(
                {"title", "description"}
        ):
            raise ValueError("At least one field must be provided")

        return self
