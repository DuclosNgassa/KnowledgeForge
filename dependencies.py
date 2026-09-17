import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ai.embedding_provider import EmbeddingProvider
from ai.openai_provider import OpenAIEmbeddingProvider
from auth.dependencies import AccessTokenBearer
from db.database import get_db
from ingestion.loader import DocumentLoader
from repositories.document_chunk_repository import DocumentChunkRepository
from repositories.document_repository import DocumentRepository
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from repositories.user_repository import UserRepository
from services.document_chunker import DocumentChunkService
from services.document_uploader import DocumentUploader
from services.embedding_service import EmbeddingService
from services.knowledge_base_service import KnowledgeBaseService
from services.user_service import UserService
from core.settings import settings


def get_user_service(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


def get_knowledge_base_service(
        db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeBaseService:
    repository = KnowledgeBaseRepository(db)

    return KnowledgeBaseService(repository)


def get_document_uploader(
        db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentUploader:
    repository = DocumentRepository(db)
    document_chunk_service = DocumentChunkService()
    document_chunk_repository = DocumentChunkRepository(db)
    document_loader = DocumentLoader()
    return DocumentUploader(
        repository=repository,
        document_chunk_service=document_chunk_service,
        document_chunk_repository=document_chunk_repository,
        document_loader=document_loader,
        session=db
    )


def get_current_user_info(
        user_details: dict = Depends(AccessTokenBearer()),
) -> dict:
    print("user_details in dependencies: ", user_details)
    return {
        "email": user_details["user"]["email"],
        "user_id": uuid.UUID(user_details["user"]["user_id"]),
    }


def get_openai_embedding_provider(model: str = "text-embedding-3-small") -> EmbeddingProvider:
    return OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key,
        model=model,
    )


def get_embedding_service(
        session: Annotated[AsyncSession, Depends(get_db)],
) -> EmbeddingService:
    repository = DocumentChunkRepository(session)
    embedding_provider = get_openai_embedding_provider()
    return EmbeddingService(
        session=session,
        repository=repository,
        embedding_provider=embedding_provider,
    )
