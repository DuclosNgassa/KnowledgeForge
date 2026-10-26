from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)


class QueryContextualizer:
    """Rewrite follow-up questions into standalone retrieval queries."""

    def __init__(
            self,
            model: BaseChatModel,
            max_history_messages: int = 10,
    ) -> None:
        self.model = model
        self.max_history_messages = max_history_messages

    async def contextualize(
            self,
            question: str,
            history: Sequence[BaseMessage],
    ) -> str:
        """Return a standalone query without answering the question."""

        question = question.strip()

        if not question or not history:
            return question

        recent_history = history[-self.max_history_messages:]
        formatted_history = self._format_history(recent_history)

        messages = [
            SystemMessage(
                content=(
                    "You rewrite user questions into standalone search queries "
                    "for a retrieval-augmented generation system.\n"
                    "Use the conversation history only to resolve references "
                    "and missing context in the current question.\n"
                    "Preserve the user's original intent and important details.\n"
                    "Do not answer the question.\n"
                    "Do not introduce facts or assumptions that are not supported "
                    "by the conversation.\n"
                    "If the question is already standalone or starts a new topic, "
                    "preserve its meaning without forcing old context into it.\n"
                    "Return only the rewritten query, without explanations or quotes."
                )
            ),
            HumanMessage(
                content=(
                    f"Conversation history:\n{formatted_history}\n\n"
                    f"Current question:\n{question}"
                )
            ),
        ]

        response = await self.model.ainvoke(messages)
        rewritten_query = self._extract_text(response.content).strip()

        # Fall back to the original question if the model returns no text.
        return rewritten_query or question

    @staticmethod
    def _format_history(history: Sequence[BaseMessage]) -> str:
        lines: list[str] = []

        for message in history:
            if isinstance(message, HumanMessage):
                role = "User"
            elif isinstance(message, AIMessage):
                role = "Assistant"
            else:
                continue

            content = QueryContextualizer._extract_text(
                message.content
            ).strip()

            if content:
                lines.append(f"{role}: {content}")

        return "\n".join(lines)

    @staticmethod
    def _extract_text(content: str | list) -> str:
        """Handle both string and block-based LangChain message content."""

        if isinstance(content, str):
            return content

        parts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
               and block.get("type") == "text"
               and isinstance(block.get("text"), str)
        ]

        return "\n".join(parts)
