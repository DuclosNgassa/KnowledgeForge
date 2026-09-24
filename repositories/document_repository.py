from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def add(self, document: Document):
        self.db.add(document)

    async def flush(self):
        await self.db.flush()

    async def save(self, document: Document, ) -> Document:
        self.db.add(document)

        await self.db.flush()

        return document

    async def commit(self):
        await self.db.commit()

    async def refresh(self, document: Document):
        await self.db.refresh(document)

    async def rollback(self):
        await self.db.rollback()

    async def find_document_by_id(self, document_id: UUID, user_id: UUID) -> Document | None:
        statement = (select(Document)
                     .where(Document.id == document_id)
                     .where(Document.user_id == user_id))

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    async def find_document_chunk_by_id(self, document_id: UUID, user_id: UUID) -> Document | None:
        statement = (
            select(Document)
            .options(
                selectinload(Document.chunks)
            )
            .where(Document.id == document_id)
            .where(Document.user_id == user_id))

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()
