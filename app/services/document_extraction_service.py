from uuid import UUID, uuid4

from app.core.exceptions.exceptions import NotFoundException
from app.models.document_extraction import DocumentExtraction
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)


class DocumentExtractionService:

    def __init__(
            self,
            document_repository: DocumentRepository,
            document_extraction_repository: DocumentExtractionRepository,
    ):
        self.document_repository = document_repository
        self.document_extraction_repository = document_extraction_repository

    async def request_extraction(
            self,
            document_id: UUID,
            user_id: UUID,
            regenerate: bool = False,
    ) -> tuple[DocumentExtraction, bool]:

        should_schedule = True

        # Verify document ownership.
        document = await self.document_repository.find_document_by_id(
            document_id=document_id,
            user_id=user_id,
        )

        if document is None:
            raise NotFoundException(
                f"Document with id {document_id} was not found."
            )

        # Check whether an extraction already exists.
        extraction = (
            await self.document_extraction_repository.find_by_document_id(
                document_id=document_id,
            )
        )

        generation_id = uuid4()

        # Create a new extraction.
        if extraction is None:
            extraction = await self.document_extraction_repository.create(
                document_id=document_id,
                generation_id=generation_id,
            )

            return extraction, should_schedule

        # Request a new extraction generation.
        if regenerate:
            extraction = await self.document_extraction_repository.set_pending(
                document_extraction=extraction,
                generation_id=generation_id,
            )

            return extraction, should_schedule

        # Existing extraction: no background task required.
        should_schedule = False

        return extraction, should_schedule

    async def get_extraction(
            self,
            document_id: UUID,
            user_id: UUID,
    ) -> DocumentExtraction:

        # Verify document ownership.
        document = await self.document_repository.find_document_by_id(
            document_id=document_id,
            user_id=user_id,
        )

        if document is None:
            raise NotFoundException(
                f"Document with id {document_id} was not found."
            )

        extraction = (
            await self.document_extraction_repository.find_by_document_id(
                document_id=document_id,
            )
        )

        if extraction is None:
            raise NotFoundException(
                f"Document with id {document_id} has no extraction yet."
            )

        return extraction

    async def set_dispatch_failed(
            self,
            document_id: UUID,
            generation_id: UUID,
    ):
        await self.document_extraction_repository.set_dispatch_failed(
            document_id=document_id,
            generation_id=generation_id,
            error_message="Failed to enqueue extraction task.",
        )
