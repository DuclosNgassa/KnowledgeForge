from uuid import UUID

from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    session_id: UUID
