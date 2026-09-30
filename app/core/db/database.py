from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
)


class Base(DeclarativeBase):
    pass

async def close_database():
    await engine.dispose()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
