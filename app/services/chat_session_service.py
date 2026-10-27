from uuid import UUID

from fastapi import HTTPException, status

from app.models import ChatSession
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository


class ChatSessionService:

    def __init__(
            self,
            chat_session_repository: ChatSessionRepository,
            knowledge_base_repository: KnowledgeBaseRepository,
    ):
        self.repository = chat_session_repository
        self.knowledge_base_repository = knowledge_base_repository

    async def find_by_id(self, session_id: UUID) -> ChatSession | None:
        return await self.repository.find_by_id(session_id)

    async def find_by_user_id(
            self,
            user_id: UUID,
    ) -> list[ChatSession]:
        return await self.repository.find_by_user_id(user_id)

    async def create(
            self,
            user_id: UUID,
            knowledge_base_ids: list[UUID] | None = None,
    ) -> ChatSession:
        if knowledge_base_ids is not None:
            knowledge_bases = (
                await self.knowledge_base_repository
                .find_all_by_ids_and_user_id(
                    knowledge_base_ids=knowledge_base_ids,
                    user_id=user_id,
                )
            )

            if len(knowledge_bases) != len(knowledge_base_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "One or more knowledge bases do not exist "
                        "or do not belong to the current user."
                    ),
                )

        chat_session = ChatSession(
            user_id=user_id,
            knowledge_base_ids=knowledge_base_ids,
        )

        return await self.repository.save(chat_session)

    async def get_user_session(
            self,
            session_id: UUID,
            user_id: UUID,
    ) -> ChatSession | None:
        return await self.repository.find_by_session_id_and_user_id(
            session_id,
            user_id,
        )
