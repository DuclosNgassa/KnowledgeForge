from uuid import uuid4

import pytest

from app.workers import document_comparison_task as task_module
from app.schemas.document_comparison import ComparisonCriterion
from app.schemas.document_comparison import (
    DocumentComparisonResponse,
    CriterionComparisonResult,
    DocumentInsight,
)

COMPARISON_ID = uuid4()
GENERATION_ID = uuid4()


@pytest.fixture
def mock_repository():
    return AsyncMock()


@pytest.fixture
def mock_agent():
    return AsyncMock()


@pytest.fixture
def mock_comparison():
    return SimpleNamespace(
        id=COMPARISON_ID,
        generation_id=GENERATION_ID,
        criteria=["key_topics", "technologies"],
        items=[
            SimpleNamespace(document_id=uuid4()),
            SimpleNamespace(document_id=uuid4()),
        ],
    )


@pytest.fixture
def mock_inputs():
    return [
        {
            "document_id": uuid4(),
            "document_title": "Document A",
            "summary": "Summary A",
            "extraction": {"key_topics": ["AI"]},
        },
        {
            "document_id": uuid4(),
            "document_title": "Document B",
            "summary": "Summary B",
            "extraction": {"key_topics": ["Machine Learning"]},
        },
    ]


from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.workers import document_comparison_task as worker


@pytest.mark.asyncio
async def test_generate_document_comparison_successfully():
    comparison_id = uuid4()
    generation_id = uuid4()

    document_id_1 = uuid4()
    document_id_2 = uuid4()

    comparison = SimpleNamespace(
        criteria=[
            "key_topics",
            "technologies",
            "named_entities",
        ],
        items=[
            SimpleNamespace(document_id=document_id_1),
            SimpleNamespace(document_id=document_id_2),
        ],
    )

    inputs = [
        {
            "document_id": document_id_1,
            "document_title": "Document A",
            "summary": "A document about Python and FastAPI.",
            "extraction": {
                "key_topics": ["Backend development"],
                "technologies": ["Python", "FastAPI"],
                "named_entities": [],
            },
        },
        {
            "document_id": document_id_2,
            "document_title": "Document B",
            "summary": "A document about Python and Django.",
            "extraction": {
                "key_topics": ["Backend development"],
                "technologies": ["Python", "Django"],
                "named_entities": [],
            },
        },
    ]

    response = MagicMock()
    response.overview = "Both documents discuss backend development."
    response.conclusion = "Both use Python but different frameworks."
    response.model_dump.return_value = {
        "criterion_results": [],
    }

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(
        return_value=comparison
    )
    repository.find_comparison_inputs = AsyncMock(
        return_value=inputs
    )
    repository.set_completed = AsyncMock(
        return_value=True
    )

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    agent = MagicMock()
    agent.compare = AsyncMock(return_value=response)

    with (
        patch.object(
            worker,
            "AsyncSessionLocal",
            return_value=session_context,
        ),
        patch.object(
            worker,
            "DocumentComparisonRepository",
            return_value=repository,
        ),
        patch.object(
            worker,
            "document_comparison_agent",
            agent,
        ),
    ):
        result = await worker._generate_document_comparison(
            comparison_id_str=str(comparison_id),
            generation_id_str=str(generation_id),
        )

    # The comparison was claimed.
    repository.claim_for_processing.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
    )

    # The comparison inputs were loaded.
    repository.find_comparison_inputs.assert_awaited_once_with(
        comparison_id=comparison_id,
    )

    # The agent received both documents and the selected criteria.
    agent.compare.assert_awaited_once_with(
        documents=inputs,
        criteria=[
            worker.ComparisonCriterion.KEY_TOPICS,
            worker.ComparisonCriterion.TECHNOLOGIES,
            worker.ComparisonCriterion.NAMED_ENTITIES,
        ],
    )

    # The completed result was persisted.
    repository.set_completed.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
        overview=response.overview,
        conclusion=response.conclusion,
        result_data={
            "criterion_results": [],
        },
    )

    # Phase 1 and Phase 3 each commit once.
    assert db.commit.await_count == 2

    assert result is response


@pytest.mark.asyncio
async def test_generate_comparison_returns_when_claim_fails():
    mock_db = AsyncMock()
    mock_db.__aenter__.return_value = mock_db

    mock_repository = AsyncMock()
    mock_repository.claim_for_processing.return_value = None

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
        ) as session_factory,
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            return_value=mock_repository,
        ),
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
        ) as compare_mock,
    ):
        session_factory.return_value.__aenter__.return_value = mock_db

        result = await task_module._generate_document_comparison(
            comparison_id_str=str(COMPARISON_ID),
            generation_id_str=str(GENERATION_ID),
        )

    assert result is None

    mock_repository.claim_for_processing.assert_awaited_once_with(
        comparison_id=COMPARISON_ID,
        generation_id=GENERATION_ID,
    )

    mock_repository.find_comparison_inputs.assert_not_awaited()
    compare_mock.assert_not_awaited()


@pytest.fixture
def mock_comparison_response():
    return DocumentComparisonResponse(
        overview="Both documents discuss AI.",
        criterion_results=[
            CriterionComparisonResult(
                criterion=ComparisonCriterion.KEY_TOPICS,
                similarities=["Both discuss artificial intelligence."],
                differences=["Document A focuses on RAG."],
                document_insights=[
                    DocumentInsight(
                        document_id=uuid4(),
                        document_title="Document A",
                        insights=["Focuses on RAG."],
                    ),
                    DocumentInsight(
                        document_id=uuid4(),
                        document_title="Document B",
                        insights=["Focuses on machine learning."],
                    ),
                ],
            ),
        ],
        conclusion="The documents share common AI topics.",
    )


@pytest.mark.asyncio
async def test_generate_comparison_completes_successfully(
        mock_comparison,
        mock_inputs,
        mock_comparison_response,
):
    mock_db = AsyncMock()

    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(
        return_value=mock_db
    )
    mock_session_context.__aexit__ = AsyncMock(
        return_value=None
    )

    mock_repository = AsyncMock()

    mock_repository.claim_for_processing.return_value = (
        mock_comparison
    )

    mock_repository.find_comparison_inputs.return_value = (
        mock_inputs
    )

    mock_repository.set_completed.return_value = True

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
            return_value=mock_session_context,
        ),
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            return_value=mock_repository,
        ),
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
            return_value=mock_comparison_response,
        ) as compare_mock,
    ):
        result = await task_module._generate_document_comparison(
            comparison_id_str=str(COMPARISON_ID),
            generation_id_str=str(GENERATION_ID),
        )

    assert result == mock_comparison_response

    compare_mock.assert_awaited_once_with(
        documents=[
            {
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "summary": item["summary"],
                "extraction": item["extraction"],
            }
            for item in mock_inputs
        ],
        criteria=[
            ComparisonCriterion.KEY_TOPICS,
            ComparisonCriterion.TECHNOLOGIES,
        ],
    )

    mock_repository.set_completed.assert_awaited_once()

    completed_call = (
        mock_repository.set_completed.await_args.kwargs
    )

    assert completed_call["comparison_id"] == COMPARISON_ID
    assert completed_call["generation_id"] == GENERATION_ID
    assert completed_call["overview"] == mock_comparison_response.overview
    assert completed_call["conclusion"] == mock_comparison_response.conclusion
    assert completed_call["result_data"] == (
        mock_comparison_response.model_dump(
            mode="json",
            exclude={"overview", "conclusion"},
        )
    )

    assert mock_db.commit.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("inputs", "expected_error"),
    [
        (
                [
                    {
                        "document_id": uuid4(),
                        "document_title": "Document A",
                        "summary": None,
                        "extraction": {"key_topics": ["AI"]},
                    },
                    {
                        "document_id": uuid4(),
                        "document_title": "Document B",
                        "summary": "Summary B",
                        "extraction": {"key_topics": ["ML"]},
                    },
                ],
                "One or more documents are missing a completed summary or structured extraction.",
        ),
        (
                [
                    {
                        "document_id": uuid4(),
                        "document_title": "Document A",
                        "summary": "Summary A",
                        "extraction": None,
                    },
                    {
                        "document_id": uuid4(),
                        "document_title": "Document B",
                        "summary": "Summary B",
                        "extraction": {"key_topics": ["ML"]},
                    },
                ],
                "One or more documents are missing a completed summary or structured extraction.",
        ),
        (
                [
                    {
                        "document_id": uuid4(),
                        "document_title": "Document A",
                        "summary": "Summary A",
                        "extraction": {"key_topics": ["AI"]},
                    },
                ],
                "One or more documents are missing a completed summary or structured extraction.",
        ),
    ],
)
async def test_generate_comparison_fails_with_incomplete_prerequisites(
        mock_comparison,
        inputs,
        expected_error,
):
    mock_db = AsyncMock()

    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    mock_repository = AsyncMock()
    mock_repository.claim_for_processing.return_value = mock_comparison
    mock_repository.find_comparison_inputs.return_value = inputs
    mock_repository.set_failed.return_value = True

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
            return_value=mock_session_context,
        ),
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            return_value=mock_repository,
        ),
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
        ) as compare_mock,
    ):
        result = await task_module._generate_document_comparison(
            comparison_id_str=str(COMPARISON_ID),
            generation_id_str=str(GENERATION_ID),
        )

    assert result is None

    mock_repository.set_failed.assert_awaited_once_with(
        comparison_id=COMPARISON_ID,
        generation_id=GENERATION_ID,
        error_message=expected_error,
    )

    compare_mock.assert_not_awaited()

    assert mock_db.commit.await_count == 1


@pytest.mark.asyncio
async def test_generate_comparison_marks_failed_and_reraises_agent_exception(
        mock_comparison,
        mock_inputs,
):
    mock_db = AsyncMock()

    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    mock_repository = AsyncMock()
    mock_repository.claim_for_processing.return_value = mock_comparison
    mock_repository.find_comparison_inputs.return_value = mock_inputs
    mock_repository.set_failed.return_value = True

    agent_error = RuntimeError("Comparison agent failed")

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
            return_value=mock_session_context,
        ),
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            return_value=mock_repository,
        ),
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
            side_effect=agent_error,
        ),
    ):
        with pytest.raises(
                RuntimeError,
                match="Comparison agent failed",
        ):
            await task_module._generate_document_comparison(
                comparison_id_str=str(COMPARISON_ID),
                generation_id_str=str(GENERATION_ID),
            )

    mock_repository.set_failed.assert_awaited_once_with(
        comparison_id=COMPARISON_ID,
        generation_id=GENERATION_ID,
        error_message="Comparison agent failed",
    )

    assert mock_db.commit.await_count == 2


@pytest.mark.asyncio
async def test_generate_comparison_returns_when_result_persistence_fails(
        mock_comparison,
        mock_inputs,
        mock_comparison_response,
):
    mock_db = AsyncMock()

    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    mock_repository = AsyncMock()
    mock_repository.claim_for_processing.return_value = mock_comparison
    mock_repository.find_comparison_inputs.return_value = mock_inputs
    mock_repository.set_completed.return_value = False

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
            return_value=mock_session_context,
        ),
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            return_value=mock_repository,
        ),
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
            return_value=mock_comparison_response,
        ),
        patch.object(
            task_module.logger,
            "warning",
        ) as warning_mock,
    ):
        result = await task_module._generate_document_comparison(
            comparison_id_str=str(COMPARISON_ID),
            generation_id_str=str(GENERATION_ID),
        )

    assert result is None

    mock_repository.set_completed.assert_awaited_once()

    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_generate_comparison_reraises_persistence_exception(
        mock_comparison,
        mock_inputs,
        mock_comparison_response,
):
    # Three separate database sessions.
    mock_db_1 = AsyncMock()
    mock_db_2 = AsyncMock()
    mock_db_3 = AsyncMock()

    session_contexts = []

    for db in (mock_db_1, mock_db_2, mock_db_3):
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=db)
        context.__aexit__ = AsyncMock(return_value=None)
        session_contexts.append(context)

    # Three repositories, one for each session.
    mock_repository_1 = AsyncMock()
    mock_repository_1.claim_for_processing.return_value = mock_comparison
    mock_repository_1.find_comparison_inputs.return_value = mock_inputs

    mock_repository_2 = AsyncMock()
    mock_repository_2.set_completed.side_effect = RuntimeError(
        "Database persistence failed"
    )

    mock_repository_3 = AsyncMock()
    mock_repository_3.set_failed.return_value = True

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
            side_effect=session_contexts,
        ) as mock_session_factory,
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            side_effect=[
                mock_repository_1,
                mock_repository_2,
                mock_repository_3,
            ],
        ) as mock_repository_factory,
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
            return_value=mock_comparison_response,
        ) as mock_compare,
    ):
        with pytest.raises(
                RuntimeError,
                match="Database persistence failed",
        ):
            await task_module._generate_document_comparison(
                comparison_id_str=str(COMPARISON_ID),
                generation_id_str=str(GENERATION_ID),
            )

    # Agent and completion persistence.
    mock_compare.assert_awaited_once()
    mock_repository_2.set_completed.assert_awaited_once()

    # Failure recorded through the third repository.
    mock_repository_1.set_failed.assert_not_awaited()
    mock_repository_2.set_failed.assert_not_awaited()

    mock_repository_3.set_failed.assert_awaited_once_with(
        comparison_id=COMPARISON_ID,
        generation_id=GENERATION_ID,
        error_message="Database persistence failed",
    )

    # Verify three distinct sessions and repositories.
    assert mock_session_factory.call_count == 3
    assert mock_repository_factory.call_count == 3

    # Verify commits.
    assert mock_db_1.commit.await_count == 1
    assert mock_db_2.commit.await_count == 0
    assert mock_db_3.commit.await_count == 1


@pytest.mark.asyncio
async def test_generate_document_comparison_fails_with_incomplete_inputs():
    comparison_id = uuid4()
    generation_id = uuid4()

    comparison = SimpleNamespace(
        criteria=["key_topics"],
        items=[
            SimpleNamespace(document_id=uuid4()),
            SimpleNamespace(document_id=uuid4()),
        ],
    )

    inputs = [
        {
            "document_id": comparison.items[0].document_id,
            "document_title": "Document A",
            "summary": "A valid summary.",
            "extraction": {"key_topics": ["Backend development"]},
        },
        {
            "document_id": comparison.items[1].document_id,
            "document_title": "Document B",
            "summary": None,
            "extraction": {"key_topics": ["Backend development"]},
        },
    ]

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(return_value=comparison)
    repository.find_comparison_inputs = AsyncMock(return_value=inputs)
    repository.set_failed = AsyncMock(return_value=True)

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    agent = MagicMock()
    agent.compare = AsyncMock()

    with (
        patch.object(worker, "AsyncSessionLocal", return_value=session_context),
        patch.object(worker, "DocumentComparisonRepository", return_value=repository),
        patch.object(worker, "document_comparison_agent", agent),
    ):
        result = await worker._generate_document_comparison(
            comparison_id_str=str(comparison_id),
            generation_id_str=str(generation_id),
        )

    repository.set_failed.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
        error_message=(
            "One or more documents are missing a completed "
            "summary or structured extraction."
        ),
    )

    agent.compare.assert_not_awaited()
    db.commit.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_generate_document_comparison_fails_with_missing_extraction():
    comparison_id = uuid4()
    generation_id = uuid4()

    comparison = SimpleNamespace(
        criteria=["key_topics"],
        items=[
            SimpleNamespace(document_id=uuid4()),
            SimpleNamespace(document_id=uuid4()),
        ],
    )

    inputs = [
        {
            "document_id": comparison.items[0].document_id,
            "document_title": "Document A",
            "summary": "A valid summary.",
            "extraction": {"key_topics": ["Backend development"]},
        },
        {
            "document_id": comparison.items[1].document_id,
            "document_title": "Document B",
            "summary": "A valid summary.",
            "extraction": None,
        }
    ]

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(return_value=comparison)
    repository.find_comparison_inputs = AsyncMock(return_value=inputs)
    repository.set_failed = AsyncMock(return_value=True)

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    agent = MagicMock()
    agent.compare = AsyncMock()

    with (
        patch.object(worker, "AsyncSessionLocal", return_value=session_context),
        patch.object(worker, "DocumentComparisonRepository", return_value=repository),
        patch.object(worker, "document_comparison_agent", agent),
    ):
        result = await worker._generate_document_comparison(
            comparison_id_str=str(comparison_id),
            generation_id_str=str(generation_id),
        )

    repository.set_failed.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
        error_message=(
            "One or more documents are missing a completed "
            "summary or structured extraction."
        ),
    )

    agent.compare.assert_not_awaited()
    db.commit.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_generate_document_comparison_skips_stale_generation():
    comparison_id = uuid4()
    generation_id = uuid4()

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(return_value=None)
    repository.find_comparison_inputs = AsyncMock()
    repository.set_failed = AsyncMock()
    repository.set_completed = AsyncMock()

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    agent = MagicMock()
    agent.compare = AsyncMock()

    with (
        patch.object(worker, "AsyncSessionLocal", return_value=session_context),
        patch.object(worker, "DocumentComparisonRepository", return_value=repository),
        patch.object(worker, "document_comparison_agent", agent),
    ):
        result = await worker._generate_document_comparison(
            comparison_id_str=str(comparison_id),
            generation_id_str=str(generation_id),
        )

    assert result is None

    repository.claim_for_processing.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
    )

    repository.find_comparison_inputs.assert_not_awaited()
    repository.set_failed.assert_not_awaited()
    repository.set_completed.assert_not_awaited()
    agent.compare.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_document_comparison_handles_agent_exception():
    comparison_id = uuid4()
    generation_id = uuid4()

    comparison = SimpleNamespace(
        criteria=["key_topics"],
        items=[
            SimpleNamespace(document_id=uuid4()),
        ],
    )

    inputs = [
        {
            "document_id": comparison.items[0].document_id,
            "document_title": "Document A",
            "summary": "A valid summary.",
            "extraction": {"key_topics": ["Backend development"]},
        },
    ]

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(return_value=comparison)
    repository.find_comparison_inputs = AsyncMock(return_value=inputs)
    repository.set_failed = AsyncMock(return_value=True)

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    agent = MagicMock()
    agent.compare = AsyncMock(
        side_effect=RuntimeError("OpenAI API unavailable")
    )

    with (
        patch.object(worker, "AsyncSessionLocal", return_value=session_context),
        patch.object(worker, "DocumentComparisonRepository", return_value=repository),
        patch.object(worker, "document_comparison_agent", agent),
    ):
        with pytest.raises(
                RuntimeError,
                match="OpenAI API unavailable",
        ):
            await worker._generate_document_comparison(
                comparison_id_str=str(comparison_id),
                generation_id_str=str(generation_id),
            )

    agent.compare.assert_awaited_once()

    repository.set_failed.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
        error_message="OpenAI API unavailable",
    )

    assert db.commit.await_count == 2


@pytest.mark.asyncio
async def test_generate_document_comparison_handles_input_loading_exception():
    comparison_id = uuid4()
    generation_id = uuid4()

    comparison = SimpleNamespace(
        criteria=["key_topics"],
        items=[SimpleNamespace(document_id=uuid4())],
    )

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(return_value=comparison)
    repository.find_comparison_inputs = AsyncMock(
        side_effect=RuntimeError("Database unavailable")
    )
    repository.set_failed = AsyncMock(return_value=True)

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    agent = MagicMock()
    agent.compare = AsyncMock()

    with (
        patch.object(worker, "AsyncSessionLocal", return_value=session_context),
        patch.object(worker, "DocumentComparisonRepository", return_value=repository),
        patch.object(worker, "document_comparison_agent", agent),
    ):
        with pytest.raises(RuntimeError, match="Database unavailable"):
            await worker._generate_document_comparison(
                comparison_id_str=str(comparison_id),
                generation_id_str=str(generation_id),
            )

    repository.set_failed.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
        error_message="Database unavailable",
    )

    agent.compare.assert_not_awaited()
    assert db.commit.await_count == 1


@pytest.mark.asyncio
async def test_generate_document_comparison_returns_none_when_result_not_saved():
    comparison_id = uuid4()
    generation_id = uuid4()

    comparison = SimpleNamespace(
        criteria=["key_topics"],
        items=[SimpleNamespace(document_id=uuid4())],
    )

    inputs = [
        {
            "document_id": comparison.items[0].document_id,
            "document_title": "Document A",
            "summary": "A valid summary.",
            "extraction": {"key_topics": ["Backend development"]},
        },
    ]

    repository = MagicMock()
    repository.claim_for_processing = AsyncMock(return_value=comparison)
    repository.find_comparison_inputs = AsyncMock(return_value=inputs)
    repository.set_completed = AsyncMock(return_value=False)
    repository.set_failed = AsyncMock()

    db = MagicMock()
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    response = MagicMock()
    response.overview = "Overview"
    response.conclusion = "Conclusion"
    response.model_dump.return_value = {"criterion_results": []}

    agent = MagicMock()
    agent.compare = AsyncMock(return_value=response)

    with (
        patch.object(worker, "AsyncSessionLocal", return_value=session_context),
        patch.object(worker, "DocumentComparisonRepository", return_value=repository),
        patch.object(worker, "document_comparison_agent", agent),
    ):
        result = await worker._generate_document_comparison(
            comparison_id_str=str(comparison_id),
            generation_id_str=str(generation_id),
        )

    assert result is None

    agent.compare.assert_awaited_once()
    repository.set_completed.assert_awaited_once()
    repository.set_failed.assert_not_awaited()

    assert db.commit.await_count == 2


@pytest.mark.asyncio
async def test_generate_comparison_preserves_original_exception_when_failure_recording_fails(
        mock_comparison,
        mock_inputs,
):
    mock_db_1 = AsyncMock()
    mock_db_2 = AsyncMock()

    session_contexts = []

    for db in (mock_db_1, mock_db_2):
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=db)
        context.__aexit__ = AsyncMock(return_value=None)
        session_contexts.append(context)

    mock_repository_1 = AsyncMock()
    mock_repository_1.claim_for_processing.return_value = mock_comparison
    mock_repository_1.find_comparison_inputs.side_effect = RuntimeError(
        "Original database error"
    )

    mock_repository_2 = AsyncMock()
    mock_repository_2.set_failed.side_effect = RuntimeError(
        "Failure recording failed"
    )

    with (
        patch.object(
            task_module,
            "AsyncSessionLocal",
            side_effect=session_contexts,
        ),
        patch.object(
            task_module,
            "DocumentComparisonRepository",
            side_effect=[
                mock_repository_1,
                mock_repository_2,
            ],
        ),
        patch.object(
            task_module.document_comparison_agent,
            "compare",
            new_callable=AsyncMock,
        ) as mock_compare,
    ):
        with pytest.raises(
                RuntimeError,
                match="Original database error",
        ):
            await task_module._generate_document_comparison(
                comparison_id_str=str(COMPARISON_ID),
                generation_id_str=str(GENERATION_ID),
            )

    mock_repository_2.set_failed.assert_awaited_once()
    mock_compare.assert_not_awaited()

    assert mock_db_2.commit.await_count == 0
