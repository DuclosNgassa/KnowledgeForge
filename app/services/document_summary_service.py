from uuid import UUID, uuid4

from app.core.exceptions.exceptions import NotFoundException
from app.models import DocumentSummary
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
            regenerate: bool = False
    ) -> tuple[DocumentSummary, bool]:
        dispatch_background_task = True
        # Verify document ownership
        document = await self.document_repository.find_document_by_id(document_id=document_id, user_id=user_id)
        if document is None:
            raise NotFoundException(f"Document with id {document_id} was not found.")

        # Check whether a summary already exists
        summary = await self.document_summary_repository.find_by_document_id(document_id=document_id)

        generation_id = uuid4()

        if summary is None:
            summary = await self.document_summary_repository.create(
                document_id=document_id,
                generation_id=generation_id,
            )

            return summary, dispatch_background_task

        elif regenerate:
            summary = await self.document_summary_repository.set_pending(summary, generation_id)
            return summary, dispatch_background_task

        dispatch_background_task = False
        return summary, dispatch_background_task

    async def get_summary(self, document_id: UUID, user_id: UUID) -> DocumentSummary:

        # Verify document ownership
        document = await self.document_repository.find_document_by_id(document_id=document_id, user_id=user_id)
        if document is None:
            raise NotFoundException(f"Document with id {document_id} was not found.")

        document_summary = await self.document_summary_repository.find_by_document_id(document_id=document_id)
        if document_summary is None:
            raise NotFoundException(f"Document with id {document_id} has not summary yet.")

        return document_summary
