from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage


class AnswerGenerator:

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate_answer(
            self,
            question: str,
            contexts: list[str],
    ) -> str:
        if not contexts:
            return "I don´t have enough context to answer this question."

        context_text = "\n\n".join(
            f"[Context {index}]\n{context}"
            for index, context in enumerate(contexts, start=1)
        )

        messages = [
            SystemMessage(
                content=(
                    "You are a knowledge assistant. Answer the user´s question "
                    "using only the provided context. "
                    "Do not invent facts or use outside knowledge. "
                    "If the context do not contain enough information, "
                    "state that you can not answer based on the available context. "
                    "Be concise."
                )
            ),
            HumanMessage(
                content=(
                    f"Retrieved context:\n{context_text}\n\n"
                    f"Question:\n{question}"
                )
            ),
        ]

        response = await self.llm.ainvoke(messages)

        if not isinstance(response.content, str):
            raise TypeError("Expected the llm content to be a string")

        return response.content.strip()
