import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from agents.agent import create_agent
from core.settings import settings
from ingestion.embeddings.embedding_provider import EmbeddingProvider
from auth.dependencies import AccessTokenBearer
from db.database import get_db
from ingestion.embeddings.google_provider import GoogleEmbeddingProvider
from ingestion.embeddings.openai_provider import OpenAIEmbeddingProvider
from ingestion.ingestion_service import IngestionService
from ingestion.loaders.loader import DocumentLoader
from repositories.document_chunk_repository import DocumentChunkRepository
from repositories.document_repository import DocumentRepository
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from repositories.user_repository import UserRepository
from services.agent_service import AgentService
from ingestion.chunker.document_chunker import DocumentChunkService
from services.document_service import DocumentService
from services.document_uploader import DocumentUploader
from ingestion.embeddings.embedding_service import EmbeddingService
from services.knowledge_base_service import KnowledgeBaseService
from services.reranker.base import Reranker
from services.reranker.cohere_reranker import CohereReranker
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
) -> DocumentUploader:
    document_loader = DocumentLoader()
    return DocumentUploader(
        document_loader=document_loader,
    )


def get_ingestion_service(
        db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionService:
    document_repository = DocumentRepository(db)
    document_service = DocumentService(document_repository)
    document_chunk_repository = DocumentChunkRepository(db)
    document_chunk_service = DocumentChunkService(document_chunk_repository)
    document_loader = DocumentLoader()
    return IngestionService(
        loader=document_loader,
        chunker=document_chunk_service,
        document_service=document_service,
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
        request: Request,
        session: Annotated[AsyncSession, Depends(get_db)],
        current_user_info: dict = Depends(get_current_user_info),

) -> AgentService:
    request_id = request.state.request_id

    embedding_provider = get_google_embedding_provider()

    search_service = SearchService(
        document_chunk_repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    document_repository = DocumentRepository(session)
    document_service = DocumentService(document_repository=document_repository)
    reranker: Reranker = CohereReranker(api_key=settings.cohere_api_key)

    agent = create_agent(
        search_service=search_service,
        document_service=document_service,
        reranker=reranker,
        user_id=current_user_info["user_id"],
        request_id=request_id,
    )

    return AgentService(agent=agent)
