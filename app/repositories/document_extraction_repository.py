from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update

from app.models import DocumentExtraction
from app.models.enums import ExtractionStatus


class DocumentExtractionRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_document_id(
            self,
            document_id: UUID,
    ) -> DocumentExtraction | None:
        stmt = (
            select(DocumentExtraction)
            .where(
                DocumentExtraction.document_id == document_id
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
            self,
            document_id: UUID,
            generation_id: UUID,
    ) -> DocumentExtraction:
        extraction = DocumentExtraction(
            document_id=document_id,
            generation_id=generation_id,
            status=ExtractionStatus.PENDING,
        )

        self.db.add(extraction)
        await self.db.flush()
        await self.db.refresh(extraction)

        return extraction

    async def set_pending(
            self,
            document_extraction: DocumentExtraction,
            generation_id: UUID,
    ) -> DocumentExtraction:
        document_extraction.generation_id = generation_id
        document_extraction.status = ExtractionStatus.PENDING
        document_extraction.error_message = None

        await self.db.flush()

        return document_extraction

    async def claim_for_processing(
            self,
            document_id: UUID,
            generation_id: UUID,
    ) -> DocumentExtraction | None:
        stmt = (
            update(DocumentExtraction)
            .where(
                DocumentExtraction.document_id == document_id,
                DocumentExtraction.generation_id == generation_id,
                DocumentExtraction.status.in_([
                    ExtractionStatus.PENDING,
                    ExtractionStatus.FAILED,
                ]),
            )
            .values(
                status=ExtractionStatus.PROCESSING,
                error_message=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentExtraction)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def set_completed(
            self,
            document_id: UUID,
            generation_id: UUID,
            extraction_data: dict,
    ) -> bool:
        stmt = (
            update(DocumentExtraction)
            .where(
                DocumentExtraction.document_id == document_id,
                DocumentExtraction.generation_id == generation_id,
                DocumentExtraction.status == ExtractionStatus.PROCESSING,
            )
            .values(
                extraction_data=extraction_data,
                status=ExtractionStatus.COMPLETED,
                error_message=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentExtraction.id)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def set_failed(
            self,
            document_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        stmt = (
            update(DocumentExtraction)
            .where(
                DocumentExtraction.document_id == document_id,
                DocumentExtraction.generation_id == generation_id,
                DocumentExtraction.status == ExtractionStatus.PROCESSING,
            )
            .values(
                status=ExtractionStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentExtraction.id)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def set_dispatch_failed(
            self,
            document_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        stmt = (
            update(DocumentExtraction)
            .where(
                DocumentExtraction.document_id == document_id,
                DocumentExtraction.generation_id == generation_id,
                DocumentExtraction.status == ExtractionStatus.PENDING,
            )
            .values(
                status=ExtractionStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentExtraction.id)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
