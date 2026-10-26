from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.services.query_contextualizer import QueryContextualizer


@pytest.mark.asyncio
async def test_returns_original_question_without_history():
    model = AsyncMock()
    contextualizer = QueryContextualizer(model=model)

    result = await contextualizer.contextualize(
        question="What about fathers in Germany?",
        history=[],
    )

    assert result == "What about fathers in Germany?"
    model.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_rewrites_follow_up_using_history():
    model = AsyncMock()
    model.ainvoke.return_value = AIMessage(
        content=(
            "Parental leave eligibility and entitlements for fathers in Germany"
        )
    )
    contextualizer = QueryContextualizer(model=model)

    history = [
        HumanMessage(
            content="What does our employee handbook say about parental leave?"
        ),
        AIMessage(content="It describes eligibility and the application process."),
    ]

    result = await contextualizer.contextualize(
        question="What about fathers in Germany?",
        history=history,
    )

    assert result == (
        "Parental leave eligibility and entitlements for fathers in Germany"
    )
    model.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_falls_back_to_original_question_if_model_returns_empty():
    model = AsyncMock()
    model.ainvoke.return_value = AIMessage(content="   ")
    contextualizer = QueryContextualizer(model=model)

    history = [HumanMessage(content="Tell me about parental leave.")]

    result = await contextualizer.contextualize(
        question="What about fathers?",
        history=history,
    )

    assert result == "What about fathers?"
