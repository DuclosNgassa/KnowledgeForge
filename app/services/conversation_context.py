from contextvars import ContextVar, Token

from langchain_core.messages import BaseMessage


class ConversationContext:
    """Hold conversation history per asynchronous execution context."""

    def __init__(self) -> None:
        self._history: ContextVar[list[BaseMessage] | None] = ContextVar(
            "conversation_history",
            default=None,
        )

    @property
    def history(self) -> list[BaseMessage]:
        return self._history.get() or []

    def set_history(self, history: list[BaseMessage]) -> Token:
        return self._history.set(list(history))

    def reset_history(self, token: Token) -> None:
        self._history.reset(token)
