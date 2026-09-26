from datetime import timedelta

from fastapi import HTTPException, status

from auth.utils import hash_password, verify_password, create_access_token
from core.settings import settings
from models.user import User
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserLogin


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_email(self, user_email: str) -> User | None:
        existing_user = await self.repository.find_by_email(
            user_email
        )

        return existing_user

    async def create_user(self, user_data: UserCreate) -> User:
        existing_user = await self.get_user_by_email(
            user_data.email
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email already exists. [email={user_data.email}]",
            )
        user_data_dict = user_data.model_dump()
        plain_password = user_data_dict.pop("password")

        password_hash = hash_password(plain_password)

        new_user = User(
            **user_data_dict,
            password_hash=password_hash
        )
        return await self.repository.create_user(new_user)

    async def login(self, user_data: UserLogin) -> dict[str, str] | None:
        exists_user = await self.get_user_by_email(user_data.email)
        if exists_user:
            is_password_valid = verify_password(user_data.password, exists_user.password_hash)
            if is_password_valid:
                user_data = {
                    "email": exists_user.email,
                    "user_id": str(exists_user.id)
                }

                access_token = create_access_token(
                    user_data=user_data,
                    expiry=timedelta(days=settings.refresh_token_expiration)
                )
                refresh_token = create_access_token(
                    user_data=user_data,
                    refresh=True,
                    expiry=timedelta(days=settings.refresh_token_expiration)
                )

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": exists_user.email,
                    "user_id": str(exists_user.id)
                }

            return None  # TODO raise exception
        else:
            return None  # TODO raise exception
