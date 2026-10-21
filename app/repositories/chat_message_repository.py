from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.models.chat_message import MessageRole
from sqlalchemy import func, select


class ChatMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            session_id: UUID,
            role: MessageRole,
            content: str,
    ):
        sequence_number = await self.get_next_sequence_number(session_id)
        chat_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sequence_number=sequence_number,
        )

        self.session.add(chat_message)

        await self.session.flush()

        return chat_message

    async def get_messages_history(self, session_id: UUID, limit: int = 20) -> list[ChatMessage]:
        statement = (select(ChatMessage)
                     .where(ChatMessage.session_id == session_id)
                     .order_by(ChatMessage.sequence_number.desc())
                     .limit(limit)
                     )

        results = await self.session.execute(statement)

        messages = list(results.scalars().all())

        return list(reversed(messages))

    async def get_next_sequence_number(
            self,
            session_id: UUID,
    ) -> int:
        statement = select(
            func.coalesce(
                func.max(ChatMessage.sequence_number),
                0,
            ) + 1
        ).where(ChatMessage.session_id == session_id)

        result = await self.session.execute(statement)
        return result.scalar_one()
