from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.chat_message import MessageRole


class ChatSessionResponse(BaseModel):
    session_id: UUID


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessagesResponse(BaseModel):
    messages: list[ChatMessageResponse]
