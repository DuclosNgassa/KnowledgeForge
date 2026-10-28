from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.models import ChatMessage
from app.models.chat_message import MessageRole
from app.repositories.chat_message_repository import ChatMessageRepository


def to_langchain_message(history: list[ChatMessage]) -> list[BaseMessage]:
    messages = []
    for message in history:
        if message.role == MessageRole.USER:
            messages.append(
                HumanMessage(content=message.content)
            )
        elif message.role == MessageRole.ASSISTANT:
            messages.append(
                AIMessage(content=message.content)
            )
    return messages


class ChatMessageService:

    def __init__(self, repository: ChatMessageRepository):
        self.repository = repository

    async def add_message(
            self,
            session_id: UUID,
            role: MessageRole,
            content: str, ) -> ChatMessage:
        return await self.repository.create(
            session_id=session_id,
            role=role,
            content=content
        )

    async def add_message_pair(
            self,
            session_id: UUID,
            user_content: str,
            assistant_content: str,
    ) -> tuple[ChatMessage, ChatMessage]:
        return await self.repository.create_pair(
            session_id=session_id,
            user_content=user_content,
            assistant_content=assistant_content,
        )

    async def get_messages_history(
            self,
            session_id: UUID,
            limit: int = 20
    ) -> list[ChatMessage]:
        return await self.repository.get_messages_history(session_id=session_id, limit=limit)
