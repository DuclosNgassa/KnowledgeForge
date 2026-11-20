from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update

from app.models import DocumentExtraction, Document, DocumentSummary
from app.models.document_comparison import (
    DocumentComparison,
    DocumentComparisonItem,
)
from app.models.enums import ComparisonStatus, ExtractionStatus, SummaryStatus


class DocumentComparisonRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comparison(
            self,
            user_id: UUID,
            document_ids: list[UUID],
            title: str | None,
            criteria: list[str],
            generation_id: UUID,
    ) -> DocumentComparison:
        comparison = DocumentComparison(
            user_id=user_id,
            title=title,
            criteria=criteria,
            status=ComparisonStatus.WAITING_FOR_PREREQUISITES,
            generation_id=generation_id,
            items=[
                DocumentComparisonItem(
                    document_id=document_id,
                    position=position,
                )
                for position, document_id in enumerate(document_ids)
            ],
        )

        self.db.add(comparison)
        await self.db.flush()

        result = await self.db.execute(
            select(DocumentComparison)
            .options(selectinload(DocumentComparison.items))
            .where(DocumentComparison.id == comparison.id)
        )

        return result.scalar_one()

    async def find_by_id(
            self,
            comparison_id: UUID,
            user_id: UUID,
    ) -> DocumentComparison | None:
        result = await self.db.execute(
            select(DocumentComparison)
            .options(selectinload(DocumentComparison.items))
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def find_by_id_without_user(
            self,
            comparison_id: UUID,
    ) -> DocumentComparison | None:
        result = await self.db.execute(
            select(DocumentComparison)
            .options(selectinload(DocumentComparison.items))
            .where(DocumentComparison.id == comparison_id)
        )

        return result.scalar_one_or_none()

    async def find_waiting_comparisons_by_document_id(
            self,
            document_id: UUID,
    ) -> list[DocumentComparison]:
        result = await self.db.execute(
            select(DocumentComparison)
            .join(DocumentComparisonItem)
            .options(selectinload(DocumentComparison.items))
            .where(
                DocumentComparisonItem.document_id == document_id,
                DocumentComparison.status
                == ComparisonStatus.WAITING_FOR_PREREQUISITES,
            )
        )

        return list(result.scalars().unique().all())

    async def set_pending(
            self,
            comparison_id: UUID,
            generation_id: UUID,
    ) -> bool:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status
                == ComparisonStatus.WAITING_FOR_PREREQUISITES,
            )
            .values(
                status=ComparisonStatus.PENDING,
                error_message=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none() is not None

    async def claim_for_processing(
            self,
            comparison_id: UUID,
            generation_id: UUID,
    ) -> DocumentComparison | None:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status.in_(
                    [
                        ComparisonStatus.PENDING,
                        ComparisonStatus.PROCESSING,
                        ComparisonStatus.FAILED,
                    ]
                ),
            )
            .values(
                status=ComparisonStatus.PROCESSING,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)
        claim_id = result.scalar_one_or_none()

        if claim_id is None:
            return None

        return await self.find_by_id_without_user(comparison_id)

    async def set_completed(
            self,
            comparison_id: UUID,
            generation_id: UUID,
            overview: str,
            conclusion: str,
            result_data: dict,
    ) -> bool:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status == ComparisonStatus.PROCESSING,
            )
            .values(
                status=ComparisonStatus.COMPLETED,
                overview=overview,
                conclusion=conclusion,
                result=result_data,
                error_message=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none() is not None

    async def set_failed(
            self,
            comparison_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status == ComparisonStatus.PROCESSING,
            )
            .values(
                status=ComparisonStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none() is not None

    async def set_dispatch_failed(
            self,
            comparison_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status.in_(
                    [
                        ComparisonStatus.WAITING_FOR_PREREQUISITES,
                        ComparisonStatus.PENDING,
                    ]
                ),
            )
            .values(
                status=ComparisonStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none() is not None

    async def find_comparison_inputs(
            self,
            comparison_id: UUID,
    ) -> list[dict]:
        statement = (
            select(
                DocumentComparisonItem.document_id,
                Document.title.label("document_title"),
                DocumentSummary.content.label("summary"),
                DocumentExtraction.extraction_data.label("extraction"),
            )
            .join(
                Document,
                Document.id == DocumentComparisonItem.document_id,
            )
            .outerjoin(
                DocumentSummary,
                and_(
                    DocumentSummary.document_id == Document.id,
                    DocumentSummary.status == SummaryStatus.COMPLETED,
                ),
            )
            .outerjoin(
                DocumentExtraction,
                and_(
                    DocumentExtraction.document_id == Document.id,
                    DocumentExtraction.status == ExtractionStatus.COMPLETED,
                ),
            )
            .where(
                DocumentComparisonItem.comparison_id == comparison_id,
            )
            .order_by(DocumentComparisonItem.position)
        )

        result = await self.db.execute(statement)

        return [
            {
                "document_id": row.document_id,
                "document_title": row.document_title,
                "summary": row.summary,
                "extraction": row.extraction,
            }
            for row in result.all()
        ]

    async def set_failed(
            self,
            comparison_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status
                == ComparisonStatus.WAITING_FOR_PREREQUISITES,
            )
            .values(
                status=ComparisonStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)
        return result.scalar_one_or_none() is not None

    async def set_failed_due_to_prerequisite(
            self,
            comparison_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        statement = (
            update(DocumentComparison)
            .where(
                DocumentComparison.id == comparison_id,
                DocumentComparison.generation_id == generation_id,
                DocumentComparison.status
                == ComparisonStatus.WAITING_FOR_PREREQUISITES,
            )
            .values(
                status=ComparisonStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(DocumentComparison.id)
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none() is not None
