from typing import Annotated

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from repositories.user_repository import UserRepository
from schemas.user import UserResponse, UserCreate, UserLogin
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


@router.post("/login",
             response_model=str,
             status_code=status.HTTP_200_OK
             )
async def login_user(user_data: UserLogin,
                     db: Annotated[AsyncSession, Depends(get_db)]) -> JSONResponse:
    repository = UserRepository(db)
    service = UserService(repository)
    token_dict = await service.login(user_data)
    print("token_dict", token_dict)
    if token_dict is not None:
        return JSONResponse(
            content={
                "message": "Login successful",
                "status_code": status.HTTP_200_OK,
                "access_token": token_dict["access_token"],
                "refresh_token": token_dict["refresh_token"],
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password or email"
        )
