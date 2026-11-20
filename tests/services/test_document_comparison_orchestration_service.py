from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.exceptions.exceptions import NotFoundException
from app.models.document_comparison import ComparisonStatus
from app.schemas.document_comparison import (
    ComparisonCriterion,
    CreateDocumentComparisonRequest, PrerequisiteDispatch,
)
from app.services.document_comparison_orchestration_service import (
    DocumentComparisonOrchestrationService,
)

TEST_USER_ID = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")

DOCUMENT_IDS = [
    UUID("f6554af6-04e4-4681-9698-569a0ef95cbf"),
    UUID("9463b82f-5b40-4a7c-9cab-6768d5e52776"),
]


def make_record():
    return SimpleNamespace(generation_id=uuid4())


def create_service(db_session):
    summary_service = SimpleNamespace(
        request_summary=AsyncMock(),
    )

    extraction_service = SimpleNamespace(
        request_extraction=AsyncMock(),
    )

    service = DocumentComparisonOrchestrationService(
        db=db_session,
        summary_service=summary_service,
        extraction_service=extraction_service,
    )

    return service, summary_service, extraction_service


def create_request():
    return CreateDocumentComparisonRequest(
        document_ids=DOCUMENT_IDS,
        title="Test comparison",
        criteria=[
            ComparisonCriterion.KEY_TOPICS,
            ComparisonCriterion.TECHNOLOGIES,
        ],
    )


@pytest.mark.asyncio
async def test_create_comparison_dispatches_missing_prerequisites(db_session):
    service, summary_service, extraction_service = create_service(db_session)

    summary_records = {
        document_id: make_record()
        for document_id in DOCUMENT_IDS
    }
    extraction_records = {
        document_id: make_record()
        for document_id in DOCUMENT_IDS
    }

    summary_service.request_summary.side_effect = [
        (summary_records[document_id], True)
        for document_id in DOCUMENT_IDS
    ]

    extraction_service.request_extraction.side_effect = [
        (extraction_records[document_id], True)
        for document_id in DOCUMENT_IDS
    ]

    comparison, dispatches = await service.create_comparison(
        request=create_request(),
        user_id=TEST_USER_ID,
    )

    assert comparison.status == ComparisonStatus.WAITING_FOR_PREREQUISITES
    assert comparison.user_id == TEST_USER_ID
    assert comparison.title == "Test comparison"
    assert comparison.criteria == ["key_topics", "technologies"]
    assert comparison.generation_id is not None

    assert len(dispatches) == 2

    for index, dispatch in enumerate(dispatches):
        document_id = DOCUMENT_IDS[index]

        assert dispatch.document_id == document_id
        assert dispatch.summary_generation_id == (
            summary_records[document_id].generation_id
        )
        assert dispatch.extraction_generation_id == (
            extraction_records[document_id].generation_id
        )

    assert summary_service.request_summary.await_count == 2
    assert extraction_service.request_extraction.await_count == 2


@pytest.mark.asyncio
async def test_create_comparison_dispatches_only_missing_summary(db_session):
    service, summary_service, extraction_service = create_service(db_session)

    summary_records = [
        make_record(),
        make_record(),
    ]

    extraction_records = [
        make_record(),
        make_record(),
    ]

    summary_service.request_summary.side_effect = [
        (summary_records[0], False),
        (summary_records[1], True),
    ]

    extraction_service.request_extraction.side_effect = [
        (extraction_records[0], False),
        (extraction_records[1], False),
    ]

    comparison, dispatches = await service.create_comparison(
        request=create_request(),
        user_id=TEST_USER_ID,
    )

    assert comparison.status == ComparisonStatus.WAITING_FOR_PREREQUISITES

    assert len(dispatches) == 1
    assert dispatches[0].document_id == DOCUMENT_IDS[1]
    assert dispatches[0].summary_generation_id == (
        summary_records[1].generation_id
    )
    assert dispatches[0].extraction_generation_id is None


@pytest.mark.asyncio
async def test_create_comparison_dispatches_only_missing_extraction(db_session):
    service, summary_service, extraction_service = create_service(db_session)

    summary_records = [
        make_record(),
        make_record(),
    ]

    extraction_records = [
        make_record(),
        make_record(),
    ]

    summary_service.request_summary.side_effect = [
        (summary_records[0], False),
        (summary_records[1], False),
    ]

    extraction_service.request_extraction.side_effect = [
        (extraction_records[0], True),
        (extraction_records[1], False),
    ]

    comparison, dispatches = await service.create_comparison(
        request=create_request(),
        user_id=TEST_USER_ID,
    )

    assert comparison.status == ComparisonStatus.WAITING_FOR_PREREQUISITES

    assert len(dispatches) == 1
    assert dispatches[0].document_id == DOCUMENT_IDS[0]
    assert dispatches[0].summary_generation_id is None
    assert dispatches[0].extraction_generation_id == (
        extraction_records[0].generation_id
    )


@pytest.mark.asyncio
async def test_create_comparison_has_no_dispatches_when_prerequisites_exist(
        db_session,
):
    service, summary_service, extraction_service = create_service(db_session)

    summary_service.request_summary.return_value = (make_record(), False)
    extraction_service.request_extraction.return_value = (make_record(), False)

    comparison, dispatches = await service.create_comparison(
        request=create_request(),
        user_id=TEST_USER_ID,
    )

    assert comparison.status == ComparisonStatus.WAITING_FOR_PREREQUISITES
    assert dispatches == []

    assert summary_service.request_summary.await_count == 2
    assert extraction_service.request_extraction.await_count == 2


@pytest.mark.asyncio
async def test_create_comparison_preserves_document_order(db_session):
    service, summary_service, extraction_service = create_service(db_session)

    summary_service.request_summary.return_value = (make_record(), False)
    extraction_service.request_extraction.return_value = (make_record(), False)

    comparison, _ = await service.create_comparison(
        request=create_request(),
        user_id=TEST_USER_ID,
    )

    # Verify the persisted item order through the repository.
    stored_comparison = await service.comparison_repository.find_by_id(
        comparison_id=comparison.id,
        user_id=TEST_USER_ID,
    )

    assert [item.document_id for item in stored_comparison.items] == DOCUMENT_IDS


@pytest.mark.asyncio
async def test_create_comparison_propagates_prerequisite_error(db_session):
    service, summary_service, extraction_service = create_service(db_session)

    summary_service.request_summary.return_value = (make_record(), False)
    extraction_service.request_extraction.side_effect = RuntimeError(
        "Extraction request failed"
    )

    with pytest.raises(RuntimeError, match="Extraction request failed"):
        await service.create_comparison(
            request=create_request(),
            user_id=TEST_USER_ID,
        )


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_when_comparison_missing(
        db_session,
):
    service, _, _ = create_service(db_session)

    service.comparison_repository.find_by_id_without_user = AsyncMock(
        return_value=None
    )

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=uuid4(),
        generation_id=uuid4(),
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_prerequisites_sets_pending_when_all_completed(
        db_session,
):
    service, _, _ = create_service(db_session)

    comparison_id = uuid4()
    generation_id = uuid4()

    comparison = SimpleNamespace(
        items=[
            SimpleNamespace(document_id=document_id)
            for document_id in DOCUMENT_IDS
        ]
    )

    service.comparison_repository.find_by_id_without_user = AsyncMock(
        return_value=comparison
    )

    service.summary_repository.find_completed_document_ids = AsyncMock(
        return_value=DOCUMENT_IDS
    )

    service.extraction_repository.find_completed_document_ids = AsyncMock(
        return_value=DOCUMENT_IDS
    )

    service.comparison_repository.set_pending = AsyncMock(
        return_value=True
    )

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison_id,
        generation_id=generation_id,
    )

    assert result is True

    service.comparison_repository.set_pending.assert_awaited_once_with(
        comparison_id=comparison_id,
        generation_id=generation_id,
    )


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_when_summary_missing(
        db_session,
):
    service, _, _ = create_service(db_session)

    comparison = SimpleNamespace(
        items=[
            SimpleNamespace(document_id=document_id)
            for document_id in DOCUMENT_IDS
        ]
    )

    service.comparison_repository.find_by_id_without_user = AsyncMock(
        return_value=comparison
    )

    service.summary_repository.find_completed_document_ids = AsyncMock(
        return_value=DOCUMENT_IDS[:1]
    )

    service.extraction_repository.find_completed_document_ids = AsyncMock(
        return_value=DOCUMENT_IDS
    )

    service.comparison_repository.set_pending = AsyncMock()

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=uuid4(),
        generation_id=uuid4(),
    )

    assert result is False
    service.comparison_repository.set_pending.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_when_extraction_missing(
        db_session,
):
    service, _, _ = create_service(db_session)

    comparison = SimpleNamespace(
        items=[
            SimpleNamespace(document_id=document_id)
            for document_id in DOCUMENT_IDS
        ]
    )

    service.comparison_repository.find_by_id_without_user = AsyncMock(
        return_value=comparison
    )

    service.summary_repository.find_completed_document_ids = AsyncMock(
        return_value=DOCUMENT_IDS
    )

    service.extraction_repository.find_completed_document_ids = AsyncMock(
        return_value=DOCUMENT_IDS[:1]
    )

    service.comparison_repository.set_pending = AsyncMock()

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=uuid4(),
        generation_id=uuid4(),
    )

    assert result is False
    service.comparison_repository.set_pending.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_comparison_rejects_documents_not_owned_by_user():
    user_id = uuid4()
    document_ids = [uuid4(), uuid4()]

    request = CreateDocumentComparisonRequest(
        document_ids=document_ids,
        title="Test comparison",
    )

    db = AsyncMock()
    summary_service = AsyncMock()
    extraction_service = AsyncMock()

    service = DocumentComparisonOrchestrationService(
        db=db,
        summary_service=summary_service,
        extraction_service=extraction_service,
    )

    service.document_repository = AsyncMock()
    service.comparison_repository = AsyncMock()

    service.document_repository.find_owned_document_ids.return_value = {
        document_ids[0]
    }

    with pytest.raises(NotFoundException):
        await service.create_comparison(
            request=request,
            user_id=user_id,
        )

    service.comparison_repository.create_comparison.assert_not_awaited()
    summary_service.request_summary.assert_not_awaited()
    extraction_service.request_extraction.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_comparison_creates_comparison_when_all_documents_are_owned():
    user_id = uuid4()
    document_ids = [uuid4(), uuid4()]
    generation_id = uuid4()

    request = CreateDocumentComparisonRequest(
        document_ids=document_ids,
        title="Test comparison",
    )

    db = AsyncMock()
    summary_service = AsyncMock()
    extraction_service = AsyncMock()

    service = DocumentComparisonOrchestrationService(
        db=db,
        summary_service=summary_service,
        extraction_service=extraction_service,
    )

    service.document_repository = AsyncMock()
    service.comparison_repository = AsyncMock()

    service.document_repository.find_owned_document_ids.return_value = set(
        document_ids
    )

    comparison = MagicMock()
    service.comparison_repository.create_comparison.return_value = comparison

    prerequisite_dispatches = [
        PrerequisiteDispatch(document_id=document_ids[0])
    ]
    service.ensure_document_prerequisites = AsyncMock(
        return_value=prerequisite_dispatches
    )

    result, dispatches = await service.create_comparison(
        request=request,
        user_id=user_id,
    )

    assert result is comparison
    assert dispatches == prerequisite_dispatches

    service.document_repository.find_owned_document_ids.assert_awaited_once_with(
        document_ids=document_ids,
        user_id=user_id,
    )

    service.comparison_repository.create_comparison.assert_awaited_once_with(
        user_id=user_id,
        document_ids=document_ids,
        title=request.title,
        criteria=[criterion.value for criterion in request.criteria],
        generation_id=service.comparison_repository.create_comparison.await_args.kwargs[
            "generation_id"
        ],
    )

    service.ensure_document_prerequisites.assert_awaited_once_with(
        document_ids=document_ids,
        user_id=user_id,
    )
