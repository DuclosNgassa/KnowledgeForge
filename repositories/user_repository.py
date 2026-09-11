from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def find_by_email(self, email:str) -> User | None:
        statement = select(User).where(User.email == email)

        return await self.db.scalar(statement)


    async def create_user(self, user:User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user