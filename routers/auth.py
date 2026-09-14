from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.responses import JSONResponse

from auth.dependencies import RefreshTokenBearer, AccessTokenBearer
from auth.utils import create_access_token
from db.redis import add_jti_to_block_list
from dependencies import get_user_service
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
        service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponse:
    new_user = await service.create_user(user_data)
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        created_at=new_user.created_at
    )


@router.post("/login",
             response_model=str,
             status_code=status.HTTP_200_OK
             )
async def login_user(user_data: UserLogin,
                     service: Annotated[UserService, Depends(get_user_service)]
                     ) -> JSONResponse:
    token_dict = await service.login(user_data)
    print("token_dict", token_dict)
    if token_dict is not None:
        return JSONResponse(
            content={
                "message": "Login successful",
                "status_code": status.HTTP_200_OK,
                "access_token": token_dict["access_token"],
                "refresh_token": token_dict["refresh_token"],
                "user": {
                    "email": token_dict["email"],
                    "user_id": token_dict["user_id"],
                }
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password or email"
        )


@router.get("/refresh_token", )
async def get_refresh_token(token_details: dict = Depends(RefreshTokenBearer())):
    print("token_details", token_details)
    expiry_timestamp = token_details["exp"]
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])
        return JSONResponse(
            content={
                "access_token": new_access_token,
            }
        )
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")


@router.get("/logout")
async def logout(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_block_list(jti)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Successfully logged out"}
    )
