from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.models.chat_message import MessageRole
from sqlalchemy import func, select

from app.models import ChatSession


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

    async def create_pair(
            self,
            session_id: UUID,
            user_content: str,
            assistant_content: str,
    ) -> tuple[ChatMessage, ChatMessage]:
        await self.lock_session(session_id)
        first_sequence_number = await self.get_next_sequence_number(
            session_id
        )

        user_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_content,
            sequence_number=first_sequence_number,
        )

        assistant_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            sequence_number=first_sequence_number + 1,
        )

        self.session.add_all([user_message, assistant_message])

        # Execute both INSERTs without committing the transaction.
        await self.session.flush()

        return user_message, assistant_message

    async def lock_session(self, session_id: UUID) -> None:
        statement = (
            select(ChatSession.id)
            .where(ChatSession.id == session_id)
            .with_for_update()
        )
        result = await self.session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ValueError(f"Chat session not found: {session_id}")
