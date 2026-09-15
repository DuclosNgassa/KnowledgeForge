from uuid import UUID

from sqlalchemy import select, delete
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
            user_id: UUID,
    ) -> KnowledgeBase | None:
        statement = select(KnowledgeBase).where(
            KnowledgeBase.name == name,
            KnowledgeBase.user_id == user_id,
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    async def find_by_id(self, knowledge_id: UUID) -> KnowledgeBase | None:
        statement = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_id)

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    async def find_all(self, user_id: UUID) -> list[KnowledgeBase]:
        statement = (select(KnowledgeBase)
                     .where(KnowledgeBase.user_id == user_id)
                     .order_by(KnowledgeBase.created_at.desc()))

        result = await self.db.scalars(
            statement
        )

        return list(result.all())

    async def update(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        await self.db.commit()
        await self.db.refresh(knowledge_base)

        return knowledge_base

    async def delete(self, knowledge_base_id: UUID, user_id: UUID) -> bool:
        statement = delete(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == user_id,
        )

        result = await self.db.execute(
            statement
        )
        await self.db.commit()

        return result.rowcount > 0
