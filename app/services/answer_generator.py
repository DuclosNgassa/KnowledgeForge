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
            return "I don't have enough context to answer this question."

        context_text = "\n\n".join(
            f"[D{index}]\n{context}"
            for index, context in enumerate(contexts, start=1)
        )

        messages = [
            SystemMessage(
                content=(
                    "You are a knowledge assistant. Answer using only the provided context. "
                    "Do not invent facts or use outside knowledge. "
                    "Cite every factual claim using the corresponding source ID, "
                    "for example [D1] or [D2]. "
                    "Place citations immediately after the claims they support. "
                    "Use only the source IDs provided in the context. "
                    "If the context does not contain enough information, state that "
                    "you cannot answer based on the available context. Be concise."
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
            raise TypeError("Expected the LLM content to be a string")

        return response.content.strip()
