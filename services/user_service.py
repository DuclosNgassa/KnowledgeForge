from fastapi import HTTPException, status

from auth.utils import generate_passwd_hash
from models.user import User
from repositories.user_repository import UserRepository
from schemas.user import UserCreate


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository


    async def get_user_by_email(self, email: str) -> User | None:
        existing_user = await self.repository.find_by_email(
            email
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

        password_hash = generate_passwd_hash(plain_password)

        new_user = User(
            **user_data_dict,
            password_hash=password_hash
        )
        return await self.repository.create_user(new_user)