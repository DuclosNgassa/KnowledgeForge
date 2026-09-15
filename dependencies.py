from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import AccessTokenBearer
from db.database import get_db
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from repositories.user_repository import UserRepository
from services.knowledge_base_service import KnowledgeBaseService
from services.user_service import UserService


def get_user_service(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


def get_knowledge_base_service(
        db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeBaseService:
    repository = KnowledgeBaseRepository(db)

    return KnowledgeBaseService(repository)


def get_current_user_info(
        user_details: dict = Depends(AccessTokenBearer()),
) -> dict:
    print("user_details in dependencies: ", user_details)
    return {
        "email": user_details["email"],
        "user_id": user_details["user_id"],
    }
