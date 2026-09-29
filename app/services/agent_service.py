from langchain_core.messages import HumanMessage
from langfuse._client.propagation import propagate_attributes

from app.models import ChatSession
from app.observability.langfuse import langfuse
from app.schemas.agent_response import AgentResponse
from langfuse.langchain import CallbackHandler


class AgentService:
    def __init__(self, agent):
        self.agent = agent

    async def chat(self,
                   message: str,
                   chat_session: ChatSession,
                   ) -> AgentResponse:
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
                        "messages": [
                            HumanMessage(content=message)
                        ]
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
                    ]
                }
            )
            return agent_response
