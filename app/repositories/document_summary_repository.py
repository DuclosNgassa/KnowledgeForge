from datetime import timezone, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentSummary
from app.models.enums import SummaryStatus


class DocumentSummaryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_document_id(self, document_id: UUID) -> DocumentSummary | None:
        stmt = select(DocumentSummary).where(
            DocumentSummary.document_id == document_id
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def create(self, document_id: UUID) -> DocumentSummary:
        document_summary = DocumentSummary(document_id=document_id, status=SummaryStatus.PENDING)
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

    async def set_pending(self, document_summary: DocumentSummary) -> DocumentSummary:
        document_summary.status = SummaryStatus.PENDING
        document_summary.error_message = None
        await self.db.flush()
        await self.db.refresh(document_summary)

        return document_summary

    async def set_completed(self, document_summary: DocumentSummary, content: str) -> DocumentSummary:
        document_summary.status = SummaryStatus.COMPLETED
        document_summary.content = content
        document_summary.error_message = None

        await self.db.flush()
        await self.db.refresh(document_summary)

        return document_summary

    async def set_failed(self, document_summary: DocumentSummary, error_message: str) -> DocumentSummary:
        document_summary.status = SummaryStatus.FAILED
        document_summary.error_message = error_message

        await self.db.flush()
        await self.db.refresh(document_summary)

        return document_summary

    async def claim_for_processing(
            self,
            document_id: UUID,
    ) -> DocumentSummary | None:
        stmt = (
            update(DocumentSummary)
            .where(
                DocumentSummary.document_id == document_id,
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
