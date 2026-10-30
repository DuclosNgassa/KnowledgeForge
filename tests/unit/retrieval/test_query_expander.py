from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.query_expander import ExpandedQueries, QueryExpander


@pytest.fixture
def mock_model():
    model = MagicMock()
    structured_model = MagicMock()

    model.with_structured_output.return_value = structured_model

    return model, structured_model


@pytest.mark.asyncio
async def test_expand_returns_original_and_alternatives(mock_model):
    model, structured_model = mock_model

    structured_model.ainvoke = AsyncMock(
        return_value=ExpandedQueries(
            queries=[
                "Parental leave for fathers in Germany",
                "Elterngeld eligibility for fathers",
            ]
        )
    )

    expander = QueryExpander(model)

    queries = await expander.expand(
        "What benefits do fathers get during parental leave?"
    )

    assert len(queries) == 3
    assert queries[0] == (
        "What benefits do fathers get during parental leave?"
    )
    assert queries[1] == "Parental leave for fathers in Germany"
    assert queries[2] == "Elterngeld eligibility for fathers"


@pytest.mark.asyncio
async def test_expand_removes_duplicates(mock_model):
    model, structured_model = mock_model

    structured_model.ainvoke = AsyncMock(
        return_value=ExpandedQueries(
            queries=[
                "Parental leave in Germany",
                "parental leave in germany",
            ]
        )
    )

    expander = QueryExpander(model)

    queries = await expander.expand("Parental leave in Germany")

    assert queries == ["Parental leave in Germany"]


@pytest.mark.asyncio
async def test_expand_falls_back_on_model_error(mock_model):
    model, structured_model = mock_model

    structured_model.ainvoke = AsyncMock(
        side_effect=RuntimeError("LLM unavailable")
    )

    expander = QueryExpander(model)

    queries = await expander.expand("My original question")

    assert queries == ["My original question"]


@pytest.mark.asyncio
async def test_expand_empty_query(mock_model):
    model, _ = mock_model

    expander = QueryExpander(model)

    assert await expander.expand("   ") == []
