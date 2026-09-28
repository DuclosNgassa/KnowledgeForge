from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
)


async def init_database():
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    await engine.dispose()


SessionLocal = async_sessionmaker(
    expire_on_commit=False,
    bind=engine,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session