from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from repositories.user_repository import UserRepository
from services.user_service import UserService


def get_user_service(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)
