import uuid
from datetime import datetime

from fastapi import HTTPException, status

from models.knowledge_base import KnowledgeBase
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate


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
                status_code=status.HTTP_409_CONFLICT,
                detail="KnowledgeBase with this name already exists",
            )

        knowledge_base = KnowledgeBase(
            name=data.name,
            user_id=user_id,
        )

        return await self.repository.create(knowledge_base)

    async def update_knowledge_base(self,
                                    knowledge_base_id: uuid.UUID,
                                    data: KnowledgeBaseUpdate,
                                    user_id: uuid.UUID) -> KnowledgeBase:
        knowledge_base_to_update = await self.repository.find_by_id(knowledge_base_id)
        if not knowledge_base_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KnowledgeBase not found")

        print("knowledge_base_to_update.user_id: ", knowledge_base_to_update.user_id)
        print(type(knowledge_base_to_update.user_id))
        print("---")
        print("user_id: ", user_id)
        print(type(user_id))

        if knowledge_base_to_update.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this knowledge base",
            )

        existing = await self.repository.find_by_name_and_user(name=data.name, user_id=user_id)
        if existing and existing.id != knowledge_base_to_update.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="KnowledgeBase name already exists")

        knowledge_base_to_update.name = data.name
        knowledge_base_to_update.updated_at = datetime.now()

        updated_knowledge_base = await self.repository.update(knowledge_base_to_update)

        return updated_knowledge_base
