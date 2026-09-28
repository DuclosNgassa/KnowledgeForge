from langchain_core.messages import HumanMessage

from app.models import ChatSession
from app.observability.langfuse import langfuse_handler


class AgentService:
    def __init__(self, agent):
        self.agent = agent

    async def chat(self,
                   message: str,
                   chat_session: ChatSession,
                   ) -> str:
        result = await self.agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content=message)
                ]
            },
            config={
                "callbacks": [langfuse_handler],
                "metadata": {
                    "langfuse_session_id": str(chat_session.id),
                    "langfuse_user_id": str(chat_session.user_id),
                }
            }
        )

        return result["structured_response"]
