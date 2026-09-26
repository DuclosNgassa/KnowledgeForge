from langchain_core.messages import HumanMessage


class AgentService:
    def __init__(self, agent):
        self.agent = agent

    async def chat(self,
                   message: str,
                   ) -> str:
        result = await self.agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content=message)
                ]
            }
        )

        return result["structured_response"]
