from typing import Any
from uuid import UUID

from models import Document
from repositories.document_repository import DocumentRepository


class DocumentService:

    def __init__(self,
                 document_repository: DocumentRepository
                 ):
        self.document_repository = document_repository

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
