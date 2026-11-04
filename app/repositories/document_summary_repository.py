from datetime import timezone, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentSummary
from app.models.enums import SummaryStatus
from app.observability.logging import logger


class DocumentSummaryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_document_id(self, document_id: UUID) -> DocumentSummary | None:
        stmt = select(DocumentSummary).where(
            DocumentSummary.document_id == document_id
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def create(
            self,
            document_id: UUID,
            generation_id: UUID,
    ) -> DocumentSummary:
        document_summary = DocumentSummary(
            document_id=document_id,
            generation_id=generation_id,
            status=SummaryStatus.PENDING,
        )
        self.db.add(document_summary)
        await self.db.flush()
        await self.db.refresh(document_summary)

        return document_summary

    async def set_processing(self, document_summary: DocumentSummary) -> DocumentSummary:
        document_summary.status = SummaryStatus.PROCESSING
        document_summary.error_message = None
        await self.db.flush()
        await self.db.refresh(document_summary)

        return document_summary

    async def set_pending(
            self,
            document_summary: DocumentSummary,
            generation_id: UUID,
    ) -> DocumentSummary:
        document_summary.generation_id = generation_id
        document_summary.status = SummaryStatus.PENDING
        document_summary.error_message = None

        await self.db.flush()
        await self.db.refresh(document_summary)

        return document_summary

    async def set_completed(
            self,
            document_id: UUID,
            generation_id: UUID,
            content: str,
    ) -> bool:
        stmt = (
            update(DocumentSummary)
            .where(
                DocumentSummary.document_id == document_id,
                DocumentSummary.generation_id == generation_id,
                DocumentSummary.status == SummaryStatus.PROCESSING,
            ).values(
                content=content,
                status=SummaryStatus.COMPLETED,
                error_message=None,
                updated_at=datetime.now(timezone.utc),
            ).returning(DocumentSummary.id)
        )

        result = await self.db.execute(stmt)
        updated = result.scalar_one_or_none() is not None
        logger.info(f"result.scalar_one_or_none() is not None: {updated}")
        return updated

    async def set_failed(
            self,
            document_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        stmt = (
            update(DocumentSummary)
            .where(
                DocumentSummary.document_id == document_id,
                DocumentSummary.generation_id == generation_id,
                DocumentSummary.status == SummaryStatus.PROCESSING,
            ).values(
                status=SummaryStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
        )

        result = await self.db.execute(stmt)

        return result.rowcount == 1

    async def claim_for_processing(
            self,
            document_id: UUID,
            generation_id: UUID,
    ) -> DocumentSummary | None:
        stmt = (
            update(DocumentSummary)
            .where(
                DocumentSummary.document_id == document_id,
                DocumentSummary.generation_id == generation_id,
                DocumentSummary.status.in_([
                    SummaryStatus.PENDING,
                    SummaryStatus.FAILED,
                ]),
            )
            .values(
                status=SummaryStatus.PROCESSING,
                error_message=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentSummary)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
