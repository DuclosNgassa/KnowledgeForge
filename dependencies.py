import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents.agent import create_agent
from core.settings import Settings, settings
from embeddings.embedding_provider import EmbeddingProvider
from embeddings.google_provider import GoogleEmbeddingProvider
from embeddings.openai_provider import OpenAIEmbeddingProvider
from auth.dependencies import AccessTokenBearer
from db.database import get_db
from ingestion.loader import DocumentLoader
from repositories.document_chunk_repository import DocumentChunkRepository
from repositories.document_repository import DocumentRepository
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from repositories.user_repository import UserRepository
from services.agent_service import AgentService
from services.document_chunker import DocumentChunkService
from services.document_service import DocumentService
from services.document_uploader import DocumentUploader
from services.embedding_service import EmbeddingService
from services.knowledge_base_service import KnowledgeBaseService
from services.search_service import SearchService
from services.user_service import UserService


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
    return {
        "email": user_details["user"]["email"],
        "user_id": uuid.UUID(user_details["user"]["user_id"]),
    }


def get_openai_embedding_provider(model: str = settings.openai_embedding_model) -> EmbeddingProvider:
    return OpenAIEmbeddingProvider(
        model=model,
    )


def get_google_embedding_provider(model: str = settings.google_embedding_model) -> EmbeddingProvider:
    return GoogleEmbeddingProvider(
        model=model,
    )


def get_embedding_service(
        session: Annotated[AsyncSession, Depends(get_db)],
) -> EmbeddingService:
    repository = DocumentChunkRepository(session)
    embedding_provider = get_google_embedding_provider()
    return EmbeddingService(
        session=session,
        repository=repository,
        embedding_provider=embedding_provider,
    )


def get_agent_service(
        session: Annotated[AsyncSession, Depends(get_db)],
        current_user_info: dict = Depends(get_current_user_info),

) -> AgentService:
    embedding_provider = get_google_embedding_provider()

    search_service = SearchService(
        document_chunk_repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    document_repository = DocumentRepository(session)
    document_service = DocumentService(document_repository=document_repository)

    agent = create_agent(
        search_service=search_service,
        document_service=document_service,
        user_id=current_user_info["user_id"],
    )

    return AgentService(agent=agent)
