from uuid import UUID, uuid4

from app.core.exceptions.exceptions import NotFoundException
from app.models import DocumentSummary
from app.models.enums import DocumentStatus, SummaryStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_summary_repository import DocumentSummaryRepository


class DocumentSummaryService:

    def __init__(
            self,
            document_repository: DocumentRepository,
            document_summary_repository: DocumentSummaryRepository,
    ):
        self.document_repository = document_repository
        self.document_summary_repository = document_summary_repository

    async def request_summary(
            self,
            document_id: UUID,
            user_id: UUID,
            regenerate: bool = False,
    ) -> tuple[DocumentSummary, bool]:
        should_schedule = True

        document = await self.document_repository.find_document_by_id(
            document_id=document_id,
            user_id=user_id,
        )

        if document is None:
            raise NotFoundException(
                f"Document with id {document_id} was not found."
            )

        if document.status != DocumentStatus.READY:
            raise ValueError("Document is not ready for summarization.")

        summary = await self.document_summary_repository.find_by_document_id(
            document_id=document_id,
        )

        generation_id = uuid4()

        if summary is None:
            summary = await self.document_summary_repository.create(
                document_id=document_id,
                generation_id=generation_id,
            )
            return summary, should_schedule

        if regenerate or summary.status == SummaryStatus.FAILED:
            summary = await self.document_summary_repository.set_pending(
                document_summary=summary,
                generation_id=generation_id,
            )
            return summary, should_schedule

        should_schedule = False
        return summary, should_schedule

    async def get_summary(self, document_id: UUID, user_id: UUID) -> DocumentSummary:

        # Verify document ownership
        document = await self.document_repository.find_document_by_id(document_id=document_id, user_id=user_id)
        if document is None:
            raise NotFoundException(f"Document with id {document_id} was not found.")

        document_summary = await self.document_summary_repository.find_by_document_id(document_id=document_id)
        if document_summary is None:
            raise NotFoundException(f"Document with id {document_id} has not summary yet.")

        return document_summary

    async def set_dispatch_failed(
            self,
            document_id,
            generation_id,
            error_message
    ) -> bool:
        return await self.document_summary_repository.set_dispatch_failed(
            document_id=document_id,
            generation_id=generation_id,
            error_message=error_message,
        )
