import uuid

from fastapi import HTTPException, status

from models.knowledge_base import KnowledgeBase
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from schemas.knowledge_base import KnowledgeBaseCreate


class KnowledgeBaseService:

    def __init__(self, repository: KnowledgeBaseRepository):
        self.repository = repository

    async def create_knowledge_base(
            self,
            data: KnowledgeBaseCreate,
            user_id: uuid.UUID,
    ) -> KnowledgeBase:
        existing = await self.repository.find_by_name_and_user(
            name=data.name,
            user_id=user_id,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_conflict,
                detail="KnowledgeBase with this name already exists",
            )

        knowledge_base = KnowledgeBase(
            name=data.name,
            user_id=user_id,
        )

        return await self.repository.create(knowledge_base)
