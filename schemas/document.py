from uuid import UUID

from pydantic import BaseModel, HttpUrl


class DocumentUrlRequest(BaseModel):
    url: HttpUrl
    knowledge_base_id: UUID
