import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import engine

import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import engine


@pytest_asyncio.fixture
async def db_session():
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            session = AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )

            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()

    finally:
        await engine.dispose()
