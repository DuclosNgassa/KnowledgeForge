from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ingestion.models.document_status import DocumentStatus
from app.models import Document


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

    async def find_all(self,
                       user_id: UUID,
                       offset: int,
                       limit: int,
                       status: DocumentStatus | None = None,
                       document_type: str | None = None,
                       sort_order: str = "desc",
                       ) -> list[Document]:

        filters = [
            Document.user_id == user_id,
        ]

        if status is not None:
            filters.append(Document.status == status)

        if document_type is not None:
            filters.append(Document.document_type == document_type)

        sort_column = (
            Document.created_at.asc()
            if sort_order == "asc"
            else Document.created_at.desc()
        )

        statement = (
            select(Document)
            .where(*filters)
            .order_by(sort_column, Document.id.asc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(statement)
        return list(result.scalars().all())

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

    async def set_document_to_ready(self, document_id: UUID):
        print("set_document_to_ready: ", document_id)
        await self.db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status=DocumentStatus.READY)
        )

    async def update_knowledge_base(self, document: Document, knowledge_base_id: UUID) -> Document:
        document.knowledge_base_id = knowledge_base_id

        await self.db.flush()

        return document

    async def find_documents_by_knowledge_base(
            self,
            knowledge_base_id: UUID,
            user_id: UUID,
            offset: int,
            limit: int,
            status: DocumentStatus | None = None,
            document_type: str | None = None,
            sort_order: str = "desc",
    ) -> tuple[list[Document], int]:

        filters = [
            Document.knowledge_base_id == knowledge_base_id,
            Document.user_id == user_id,
        ]

        if status is not None:
            filters.append(Document.status == status)

        if document_type is not None:
            filters.append(Document.document_type == document_type)

        sort_column = (
            Document.created_at.asc()
            if sort_order == "asc"
            else Document.created_at.desc()
        )

        statement = (
            select(Document)
            .where(*filters)
            .order_by(sort_column, Document.id.asc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(statement)
        documents = list(result.scalars().all())

        count_statement = (
            select(func.count(Document.id))
            .where(*filters)
        )

        count_result = await self.db.execute(count_statement)
        total = count_result.scalar_one()

        return documents, total

    async def update_metadata(
            self,
            document: Document,
            title: str | None,
            description: str | None,
            update_title: bool,
            update_description: bool,
    ) -> Document:
        if update_title:
            document.title = title
        if update_description:
            document.description = description

        await self.db.flush()

        return document

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.flush()
