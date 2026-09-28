from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession


class ChatSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, session_id: UUID) -> ChatSession | None:
        statement = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: UUID) -> list[ChatSession]:
        statement = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
        )

        result = await self.db.scalars(
            statement
        )

        return list(result.all())

    async def save(self, chat_session: ChatSession) -> ChatSession:
        self.db.add(chat_session)
        await self.db.commit()
        await self.db.refresh(chat_session)

        return chat_session

    async def find_by_session_id_and_user_id(self, session_id, user_id):
        statement = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .where(ChatSession.user_id == user_id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()
