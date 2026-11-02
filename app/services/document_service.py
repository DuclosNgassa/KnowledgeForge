import math
from uuid import UUID

from app.core.exceptions.exceptions import NotFoundException
from app.ingestion.models.document_status import DocumentStatus
from app.models import Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.document import UpdateDocumentMetadataRequest
from app.schemas.document_response import DocumentListResponse


class DocumentService:

    def __init__(self,
                 document_repository: DocumentRepository,
                 knowledge_base_repository: KnowledgeBaseRepository,
                 ):
        self.document_repository = document_repository
        self.knowledge_base_repository = knowledge_base_repository

    async def find_document_by_id(self, document_id: UUID, user_id: UUID) -> Document | None:
        return await self.document_repository.find_document_by_id(
            document_id=document_id,
            user_id=user_id
        )

    async def get_document_with_chunks(self, document_id: UUID, user_id: UUID) -> Document | None:
        return await self.document_repository.find_document_chunk_by_id(
            document_id=document_id,
            user_id=user_id
        )

    async def save(self, document: Document):
        await self.document_repository.save(document)

    async def update_knowledge_base(
            self,
            document_id: UUID,
            user_id: UUID,
            knowledge_base_id: UUID | None
    ) -> Document:
        document = await self.document_repository.find_document_by_id(document_id, user_id)
        if document is None:
            raise NotFoundException(f"Document not found. [document_id={document_id}]")

        if knowledge_base_id is not None:
            knowledge_base = await self.knowledge_base_repository.find_by_id(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id)

            if knowledge_base is None:
                raise NotFoundException(f"KnowledgeBase not found. [knowledge_base_id={knowledge_base_id}]")

        return await self.document_repository.update_knowledge_base(
            document=document,
            knowledge_base_id=knowledge_base_id
        )

    async def get_documents_by_knowledge_base(
            self,
            knowledge_base_id: UUID,
            user_id: UUID,
            page: int = 1,
            page_size: int = 20,
            status: DocumentStatus | None = None,
            document_type: str | None = None,
            sort_order: str = "desc",
    ) -> DocumentListResponse:
        knowledge_base = await self.knowledge_base_repository.find_by_id(
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
        )

        if knowledge_base is None:
            raise NotFoundException(f"KnowledgeBase not found. [knowledge_base_id={knowledge_base_id}]")

        offset = (page - 1) * page_size

        documents, total = (
            await self.document_repository.find_documents_by_knowledge_base(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                offset=offset,
                limit=page_size,
                status=status,
                document_type=document_type,
                sort_order=sort_order,
            )
        )

        return DocumentListResponse(
            items=documents,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )

    async def find_all(
            self,
            user_id: UUID,
            page: int = 1,
            page_size: int = 20,
            status: DocumentStatus | None = None,
            document_type: str | None = None,
            sort_order: str = "desc",
    ) -> DocumentListResponse:
        offset = (page - 1) * page_size
        documents = await self.document_repository.find_all(
            user_id=user_id,
            offset=offset,
            limit=page_size,
            status=status,
            document_type=document_type,
            sort_order=sort_order,
        )

        return DocumentListResponse(
            items=documents,
            total=len(documents),
            page=page,
            page_size=page_size,
            total_pages=math.ceil(len(documents) / page_size),
        )

    async def update_metadata(
            self,
            document_id: UUID,
            user_id: UUID,
            request: UpdateDocumentMetadataRequest,
    ) -> Document:
        document = await self.document_repository.find_document_by_id(document_id, user_id)

        if document is None:
            raise NotFoundException(f"Document not found. [document_id={document_id}]")

        return await self.document_repository.update_metadata(
            document=document,
            title=request.title,
            description=request.description,
            update_title="title" in request.model_fields_set,
            update_description="description" in request.model_fields_set,
        )

    async def delete_document(
            self,
            document_id: UUID,
            user_id: UUID,
    ) -> None:
        document = await self.document_repository.find_document_by_id(document_id, user_id)
        if document is None:
            raise NotFoundException(f"Document not found. [document_id={document_id}]")

        await self.document_repository.delete(document)
