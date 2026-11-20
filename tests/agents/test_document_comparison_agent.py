from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.document_comparison_agent import DocumentComparisonAgent
from app.schemas.document_comparison import (
    ComparisonCriterion,
    DocumentComparisonResponse,
)

DOCUMENTS = [
    {
        "document_id": "f6554af6-04e4-4681-9698-569a0ef95cbf",
        "document_title": "Document A",
        "summary": "A document about Python and FastAPI.",
        "extraction": {
            "document_category": "Technical documentation",
            "key_topics": ["Python", "API development"],
            "technologies": ["Python", "FastAPI"],
            "named_entities": [],
        },
    },
    {
        "document_id": "9463b82f-5b40-4a7c-9cab-6768d5e52776",
        "document_title": "Document B",
        "summary": "A document about Python and Django.",
        "extraction": {
            "document_category": "Technical documentation",
            "key_topics": ["Python", "Web development"],
            "technologies": ["Python", "Django"],
            "named_entities": [],
        },
    },
]


@pytest.fixture
def comparison_response():
    return DocumentComparisonResponse(
        overview="Both documents discuss Python development.",
        criterion_results=[
            {
                "criterion": ComparisonCriterion.TECHNOLOGIES,
                "similarities": [
                    "Both documents mention Python."
                ],
                "differences": [
                    "Document A mentions FastAPI, while Document B mentions Django."
                ],
                "document_insights": [
                    {
                        "document_id": DOCUMENTS[0]["document_id"],
                        "document_title": "Document A",
                        "insights": ["Uses FastAPI."],
                    },
                    {
                        "document_id": DOCUMENTS[1]["document_id"],
                        "document_title": "Document B",
                        "insights": ["Uses Django."],
                    },
                ],
            }
        ],
        conclusion="Both documents cover Python but use different frameworks.",
    )


@pytest.fixture
def model():
    return MagicMock()


@pytest.fixture
def agent(model):
    return DocumentComparisonAgent(model=model)


@pytest.mark.asyncio
async def test_compare_returns_structured_response(
        agent,
        model,
        comparison_response,
):
    structured_model = MagicMock()
    structured_model.ainvoke = AsyncMock(
        return_value=comparison_response
    )

    agent.structured_model = structured_model
    agent.chain = MagicMock()
    agent.chain.ainvoke = structured_model.ainvoke

    result = await agent.compare(
        documents=DOCUMENTS,
        criteria=[ComparisonCriterion.TECHNOLOGIES],
    )

    assert result == comparison_response
    assert isinstance(result, DocumentComparisonResponse)

    structured_model.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_compare_passes_selected_criteria(
        agent,
        comparison_response,
):
    structured_model = MagicMock()
    structured_model.ainvoke = AsyncMock(
        return_value=comparison_response
    )

    agent.chain = MagicMock()
    agent.chain.ainvoke = structured_model.ainvoke

    await agent.compare(
        documents=DOCUMENTS,
        criteria=[
            ComparisonCriterion.KEY_TOPICS,
            ComparisonCriterion.TECHNOLOGIES,
        ],
    )

    invocation = structured_model.ainvoke.await_args
    assert invocation.args[0]["criteria"] == "key_topics, technologies"


@pytest.mark.asyncio
async def test_compare_passes_document_data(
        agent,
        comparison_response,
):
    structured_model = MagicMock()
    structured_model.ainvoke = AsyncMock(
        return_value=comparison_response
    )

    agent.chain = MagicMock()
    agent.chain.ainvoke = structured_model.ainvoke

    await agent.compare(
        documents=DOCUMENTS,
        criteria=[ComparisonCriterion.TECHNOLOGIES],
    )

    invocation = structured_model.ainvoke.await_args
    documents_json = invocation.args[0]["documents"]

    assert "Document A" in documents_json
    assert "Document B" in documents_json
    assert "FastAPI" in documents_json
    assert "Django" in documents_json


@pytest.mark.asyncio
async def test_compare_propagates_model_error(agent):
    structured_model = MagicMock()
    structured_model.ainvoke = AsyncMock(
        side_effect=RuntimeError("Model invocation failed")
    )

    agent.chain = MagicMock()
    agent.chain.ainvoke = structured_model.ainvoke

    with pytest.raises(RuntimeError, match="Model invocation failed"):
        await agent.compare(
            documents=DOCUMENTS,
            criteria=[ComparisonCriterion.TECHNOLOGIES],
        )
