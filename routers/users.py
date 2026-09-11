from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Annotated
from db.database import get_db
from repositories.user_repository import UserRepository
from schemas.user import UserResponse, UserCreate
from services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def get_user_info(
        user_id: str,
        db: Annotated[AsyncSession, Depends(get_db)],
):
    pass