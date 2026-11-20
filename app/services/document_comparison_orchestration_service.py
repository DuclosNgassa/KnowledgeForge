from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import NotFoundException
from app.models import DocumentComparison
from app.repositories.document_comparison_repository import DocumentComparisonRepository
from app.repositories.document_extraction_repository import DocumentExtractionRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_summary_repository import DocumentSummaryRepository
from app.schemas.document_comparison import PrerequisiteDispatch, CreateDocumentComparisonRequest
from app.services.document_extraction_service import DocumentExtractionService
from app.services.document_summary_service import DocumentSummaryService

from uuid import UUID


class DocumentComparisonOrchestrationService:

    def __init__(
            self,
            db: AsyncSession,
            summary_service: DocumentSummaryService,
            extraction_service: DocumentExtractionService,
    ):
        self.db = db
        self.summary_service = summary_service
        self.extraction_service = extraction_service
        self.comparison_repository = DocumentComparisonRepository(db)
        self.summary_repository = DocumentSummaryRepository(db)
        self.extraction_repository = DocumentExtractionRepository(db)
        self.document_repository = DocumentRepository(db)

    async def ensure_document_prerequisites(
            self,
            document_ids: list[UUID],
            user_id: UUID,
    ) -> list[PrerequisiteDispatch]:

        dispatches = []

        for document_id in document_ids:

            summary, should_dispatch_summary = (
                await self.summary_service.request_summary(
                    document_id=document_id,
                    user_id=user_id,
                )
            )

            extraction, should_dispatch_extraction = (
                await self.extraction_service.request_extraction(
                    document_id=document_id,
                    user_id=user_id,
                )
            )

            if should_dispatch_summary or should_dispatch_extraction:
                dispatches.append(
                    PrerequisiteDispatch(
                        document_id=document_id,
                        summary_generation_id=(
                            summary.generation_id
                            if should_dispatch_summary
                            else None
                        ),
                        extraction_generation_id=(
                            extraction.generation_id
                            if should_dispatch_extraction
                            else None
                        ),
                    )
                )

        return dispatches

    async def create_comparison(
            self,
            request: CreateDocumentComparisonRequest,
            user_id: UUID,
    ):
        owned_document_ids = await self.document_repository.find_owned_document_ids(
            document_ids=request.document_ids,
            user_id=user_id,
        )

        if owned_document_ids != set(request.document_ids):
            raise NotFoundException(
                "Some documents do not exist or do not belong to the user."
            )

        generation_id = uuid4()

        comparison = await self.comparison_repository.create_comparison(
            user_id=user_id,
            document_ids=request.document_ids,
            title=request.title,
            criteria=[criterion.value for criterion in request.criteria],
            generation_id=generation_id,
        )

        prerequisite_dispatches = (
            await self.ensure_document_prerequisites(
                document_ids=request.document_ids,
                user_id=user_id,
            )
        )

        return comparison, prerequisite_dispatches

    async def check_prerequisites_and_set_pending(
            self,
            comparison_id: UUID,
            generation_id: UUID,
    ) -> bool:
        comparison = await self.comparison_repository.find_by_id_without_user(
            comparison_id=comparison_id,
        )

        if comparison is None:
            return False

        document_ids = [
            item.document_id
            for item in comparison.items
        ]

        completed_summary_ids = (
            await self.summary_repository.find_completed_document_ids(
                document_ids
            )
        )

        completed_extraction_ids = (
            await self.extraction_repository.find_completed_document_ids(
                document_ids
            )
        )

        all_summaries_completed = set(document_ids).issubset(
            completed_summary_ids
        )

        all_extractions_completed = set(document_ids).issubset(
            completed_extraction_ids
        )

        if not all_summaries_completed or not all_extractions_completed:
            return False

        return await self.comparison_repository.set_pending(
            comparison_id=comparison_id,
            generation_id=generation_id,
        )

    async def set_dispatch_failed(
            self,
            comparison_id: UUID,
            generation_id: UUID,
            error_message: str,
    ) -> bool:
        return await self.comparison_repository.set_failed(
            comparison_id=comparison_id,
            generation_id=generation_id,
            error_message=error_message,
        )

    async def fail_waiting_comparisons_for_document(
            self,
            document_id: UUID,
            error_message: str,
    ) -> int:
        comparisons = (
            await self.comparison_repository
            .find_waiting_comparisons_by_document_id(
                document_id=document_id,
            )
        )

        failed_count = 0

        for comparison in comparisons:
            updated = (
                await self.comparison_repository
                .set_failed_due_to_prerequisite(
                    comparison_id=comparison.id,
                    generation_id=comparison.generation_id,
                    error_message=error_message,
                )
            )

            if updated:
                failed_count += 1

        return failed_count

    async def get_comparison(
            self,
            comparison_id: UUID,
            user_id: UUID,
    ) -> DocumentComparison | None:
        return await self.comparison_repository.find_by_id(
            comparison_id=comparison_id,
            user_id=user_id,
        )
