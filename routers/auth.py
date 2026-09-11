from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from repositories.user_repository import UserRepository
from schemas.user import UserResponse, UserCreate
from services.user_service import UserService

router = APIRouter(
    tags=["Auth"],
    prefix="/auth",
)


@router.post("/signup",
                  response_model=UserResponse,
                  status_code=status.HTTP_201_CREATED
                  )
async def create_user_account(
        user_data: UserCreate,
        db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    repository = UserRepository(db)
    service = UserService(repository)
    new_user = await service.create_user(user_data)
    return UserResponse(id=new_user.id, username=new_user.username,
                        email=new_user.email, created_at=new_user.created_at)
