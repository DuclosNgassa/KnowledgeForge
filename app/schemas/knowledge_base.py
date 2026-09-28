import uuid
from datetime import datetime

from pydantic import BaseModel, Field

"""
{
    "name": "AI Research"
}
"""


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=255,
    )


class KnowledgeBaseUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=255,
    )


class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class KnowledgeBaseListResponse(BaseModel):
    knowledge_bases: list[KnowledgeBaseResponse]
