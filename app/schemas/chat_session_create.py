from pydantic import BaseModel, field_validator
from uuid import UUID


class ChatSessionCreate(BaseModel):
    knowledge_base_ids: list[UUID] | None = None

    @field_validator("knowledge_base_ids")
    @classmethod
    def validate_knowledge_base_ids(
            cls,
            value: list[UUID] | None,
    ) -> list[UUID] | None:
        if value is not None and not value:
            raise ValueError(
                "Select at least one knowledge base, or omit the field "
                "to search all documents."
            )

        if value is not None and len(value) != len(set(value)):
            raise ValueError("Duplicate knowledge base IDs are not allowed.")

        return value
