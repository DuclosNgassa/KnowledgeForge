from collections.abc import Awaitable, Callable, Sequence
from typing import Any


def build_retriever(
        user_id: str,
        search: Callable[..., Awaitable[Sequence[Any]]],
        limit: int = 5,
) -> Callable[[str], Awaitable[Sequence[Any]]]:
    async def retrieve(question: str) -> Sequence[Any]:
        return await search(
            query=question,
            user_id=user_id,
            limit=limit,
        )

    return retrieve
