import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
            self,
            knowledge_base: KnowledgeBase,
    ) -> KnowledgeBase:
        self.db.add(knowledge_base)
        await self.db.commit()
        await self.db.refresh(knowledge_base)

        return knowledge_base

    async def find_by_name_and_user(
            self,
            name: str,
            user_id: uuid.UUID,
    ) -> KnowledgeBase | None:
        statement = select(KnowledgeBase).where(
            KnowledgeBase.name == name,
            KnowledgeBase.user_id == user_id,
        )

        return await self.db.scalar(statement)
