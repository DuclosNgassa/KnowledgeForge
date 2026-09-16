from sqlalchemy.ext.asyncio import AsyncSession

from models import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, document: Document, ) -> Document:
        self.db.add(document)

        await self.db.commit()
        await self.db.refresh(document)

        return document
