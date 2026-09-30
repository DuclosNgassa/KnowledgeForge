from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.models.chat_message import MessageRole


class ChatMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            session_id: UUID,
            role: MessageRole,
            content: str,
    ):
        chat_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )

        self.session.add(chat_message)

        await self.session.flush()

        return chat_message

    async def get_history(self, session_id: UUID, limit: int = 20) -> list[ChatMessage]:
        statement = (select(ChatMessage)
                     .where(ChatMessage.session_id == session_id)
                     .order_by(ChatMessage.created_at.desc())
                     .limit(limit)
                     )

        results = await self.session.execute(statement)

        messages = list(results.scalars().all())

        # reverse messages to have the chronological order.
        messages.reverse()

        return messages

    async def get_messages(self, session_id: UUID, limit: int = 20) -> list[ChatMessage]:
        statement = (select(ChatMessage)
                     .where(ChatMessage.session_id == session_id)
                     .order_by(ChatMessage.created_at.asc())
                     .limit(limit)
                     )

        results = await self.session.execute(statement)

        messages = list(results.scalars().all())

        return messages
