from langchain_core.messages import HumanMessage
from langfuse._client.propagation import propagate_attributes

from app.models import ChatSession
from app.models.chat_message import MessageRole
from app.observability.langfuse import langfuse
from app.schemas.agent_response import AgentResponse
from langfuse.langchain import CallbackHandler

from app.services.chat_message_service import ChatMessageService, to_langchain_message

MAX_HISTORY_MESSAGES = 20


class AgentService:
    def __init__(
            self,
            agent,
            chat_message_service: ChatMessageService,
    ):
        self.agent = agent
        self.chat_message_service = chat_message_service

    async def chat(self,
                   message: str,
                   chat_session: ChatSession,
                   ) -> AgentResponse:
        history = await self.chat_message_service.get_history(
            session_id=chat_session.id,
            limit=MAX_HISTORY_MESSAGES,
        )

        messages = to_langchain_message(history)

        messages.append(HumanMessage(content=message))

        langfuse_handler = CallbackHandler()

        with langfuse.start_as_current_observation(
                as_type="agent",
                name="agent-chat",
                input={
                    "message": message,
                }
        ) as agent_observation:
            with propagate_attributes(
                    session_id=str(chat_session.id),
                    user_id=str(chat_session.user_id),
            ):
                response = await self.agent.ainvoke(
                    {
                        "messages": messages
                    },
                    config={
                        "callbacks": [langfuse_handler],
                    }
                )

            agent_response = response["structured_response"]

            agent_observation.update(
                output={
                    "answer": agent_response.answer,
                    "sources": [
                        source.model_dump(mode="json")
                        for source in agent_response.sources
                    ],
                }
            )

        # persist conversation
        await self.chat_message_service.add_message(
            session_id=chat_session.id,
            role=MessageRole.USER,
            content=message,
        )

        await self.chat_message_service.add_message(
            session_id=chat_session.id,
            role=MessageRole.ASSISTANT,
            content=agent_response.answer,
        )

        return agent_response
