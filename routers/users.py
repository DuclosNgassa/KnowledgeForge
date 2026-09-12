from typing import Annotated

from fastapi import APIRouter, status, Depends
from pydantic import EmailStr

from auth.dependencies import AccessTokenBearer
from dependencies import get_user_service
from schemas.user import UserResponse
from services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

access_token_bearer = AccessTokenBearer()


@router.get(
    "/{email}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_info(
        email: EmailStr,
        service: Annotated[UserService, Depends(get_user_service)],
        user_detail=Depends(access_token_bearer),
) -> UserResponse:
    print("user_detail: ", user_detail)
    user = await service.get_user_by_email(email)
    return UserResponse.model_validate(user)
