from uuid import UUID

from app.models import ChatSession
from app.repositories.chat_session_repository import ChatSessionRepository


class ChatSessionService:

    def __init__(self,
                 chat_session_repository: ChatSessionRepository,
                 ):
        self.repository = chat_session_repository

    async def find_by_id(self, session_id: UUID) -> ChatSession | None:
        return await (self
                      .repository
                      .find_by_id(session_id)
                      )

    async def find_by_user_id(self, user_id: UUID) -> list[ChatSession]:
        return await (self
                      .repository
                      .find_by_user_id(user_id)
                      )

    async def create(self, user_id: UUID) -> ChatSession:
        chat_session = ChatSession(user_id=user_id)
        return await self.repository.save(chat_session)

    async def get_user_session(self, session_id, user_id):
        return await (self
                      .repository
                      .find_by_session_id_and_user_id(session_id, user_id)
                      )
