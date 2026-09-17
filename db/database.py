from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
)

async def create_tables():
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

SessionLocal = async_sessionmaker(
    expire_on_commit=False,
    bind=engine,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session