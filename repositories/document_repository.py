from sqlalchemy.ext.asyncio import AsyncSession

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
        # await self.db.refresh(document)

        return document

    async def commit(self):
        await self.db.commit()

    async def refresh(self, document: Document):
        await self.db.refresh(document)

    async def rollback(self):
        await self.db.rollback()
