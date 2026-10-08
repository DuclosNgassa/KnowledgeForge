import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent import create_agent
from app.core.settings import settings
from app.ingestion.chunker.document_chunker import DocumentChunkService
from app.auth.dependencies import AccessTokenBearer
from app.core.db.database import get_db
from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.ingestion.embeddings.embedding_provider_type import EmbeddingProviderType
from app.ingestion.embeddings.google_provider import GoogleEmbeddingProvider
from app.ingestion.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.loaders.loader import DocumentLoader
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.user_repository import UserRepository
from app.services.agent_service import AgentService
from app.services.chat_message_service import ChatMessageService
from app.services.chat_session_service import ChatSessionService
from app.services.document_service import DocumentService
from app.services.document_uploader import DocumentUploader
from app.ingestion.embeddings.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.reranker.base import Reranker
from app.services.reranker.cohere_reranker import CohereReranker
from app.services.search_service import SearchService
from app.services.user_service import UserService


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


def get_embedding_provider(provider: EmbeddingProviderType) -> EmbeddingProvider:
    if provider == EmbeddingProviderType.GEMINI:
        return get_google_embedding_provider()
    elif provider == EmbeddingProviderType.OPENAI:
        return get_openai_embedding_provider()
    raise ValueError(f"Unknown embedding provider {provider}")


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

    #    embedding_provider = get_google_embedding_provider()
    embedding_provider = get_openai_embedding_provider()

    search_service = SearchService(
        document_chunk_repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    document_repository = DocumentRepository(session)
    document_service = DocumentService(document_repository=document_repository)

    reranker: Reranker = CohereReranker(api_key=settings.cohere_api_key)

    chat_message_service = get_chat_message_service(session)

    agent = create_agent(
        search_service=search_service,
        document_service=document_service,
        reranker=reranker,
        user_id=current_user_info["user_id"],
        request_id=request_id,
    )

    return AgentService(agent=agent, chat_message_service=chat_message_service)


def get_chat_session_service(
        db: AsyncSession = Depends(get_db),
) -> ChatSessionService:
    repository = ChatSessionRepository(db)
    return ChatSessionService(repository)


def get_chat_message_service(
        session: AsyncSession = Depends(get_db),
) -> ChatMessageService:
    repository = ChatMessageRepository(session)
    return ChatMessageService(repository)
