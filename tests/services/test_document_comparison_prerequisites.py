from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.models.document_comparison import ComparisonStatus, DocumentComparisonItem, DocumentComparison
from app.models.document_summary import DocumentSummary, SummaryStatus
from app.models.document_extraction import (
    DocumentExtraction,
    ExtractionStatus,
)
from app.repositories.document_comparison_repository import (
    DocumentComparisonRepository,
)
from app.repositories.document_summary_repository import (
    DocumentSummaryRepository,
)
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from app.services.document_comparison_orchestration_service import (
    DocumentComparisonOrchestrationService,
)

TEST_USER_ID = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")

DOCUMENT_IDS = [
    UUID("f2a7838e-f581-42cb-95c0-a4aa679bf0e4"),
    UUID("8e1b7de3-f25c-4e58-9182-1ad7ebfc9f79"),
]


async def create_comparison(db_session):
    generation_id = uuid4()

    comparison = DocumentComparison(
        user_id=TEST_USER_ID,
        title="Test comparison",
        criteria=["key_topics", "technologies", "named_entities"],
        status=ComparisonStatus.WAITING_FOR_PREREQUISITES,
        generation_id=generation_id,
    )

    db_session.add(comparison)
    await db_session.flush()

    for position, document_id in enumerate(DOCUMENT_IDS, start=1):
        db_session.add(
            DocumentComparisonItem(
                comparison_id=comparison.id,
                document_id=document_id,
                position=position,
            )
        )

    await db_session.flush()

    return comparison, generation_id


async def create_prerequisites(
        db_session,
        summary_status=SummaryStatus.COMPLETED,
        extraction_status=ExtractionStatus.COMPLETED,
):
    for document_id in DOCUMENT_IDS:
        db_session.add(
            DocumentSummary(
                document_id=document_id,
                status=summary_status,
            )
        )

        db_session.add(
            DocumentExtraction(
                document_id=document_id,
                status=extraction_status,
            )
        )

    await db_session.flush()


def create_service(db_session):
    return DocumentComparisonOrchestrationService(
        db=db_session,
        summary_service=AsyncMock(),
        extraction_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_check_prerequisites_sets_pending_when_all_completed(
        db_session,
):
    comparison, generation_id = await create_comparison(db_session)

    await create_prerequisites(db_session)

    service = create_service(db_session)

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert result is True

    updated_comparison = await service.comparison_repository.find_by_id(
        comparison_id=comparison.id,
        user_id=TEST_USER_ID,
    )

    assert updated_comparison.status == ComparisonStatus.PENDING


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_when_summary_incomplete(
        db_session,
):
    comparison, generation_id = await create_comparison(db_session)

    await create_prerequisites(
        db_session,
        summary_status=SummaryStatus.PROCESSING,
    )

    service = create_service(db_session)

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert result is False

    updated_comparison = await service.comparison_repository.find_by_id(
        comparison_id=comparison.id,
        user_id=TEST_USER_ID,
    )

    assert (
            updated_comparison.status
            == ComparisonStatus.WAITING_FOR_PREREQUISITES
    )


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_when_extraction_incomplete(
        db_session,
):
    comparison, generation_id = await create_comparison(db_session)

    await create_prerequisites(
        db_session,
        extraction_status=ExtractionStatus.FAILED,
    )

    service = create_service(db_session)

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert result is False

    updated_comparison = await service.comparison_repository.find_by_id(
        comparison_id=comparison.id,
        user_id=TEST_USER_ID,
    )

    assert (
            updated_comparison.status
            == ComparisonStatus.WAITING_FOR_PREREQUISITES
    )


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_for_missing_comparison(
        db_session,
):
    service = create_service(db_session)

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=uuid4(),
        generation_id=uuid4(),
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_for_wrong_generation_id(
        db_session,
):
    comparison, _ = await create_comparison(db_session)

    await create_prerequisites(db_session)

    service = create_service(db_session)

    result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison.id,
        generation_id=uuid4(),
    )

    assert result is False

    updated_comparison = await service.comparison_repository.find_by_id(
        comparison_id=comparison.id,
        user_id=TEST_USER_ID,
    )

    assert (
            updated_comparison.status
            == ComparisonStatus.WAITING_FOR_PREREQUISITES
    )


@pytest.mark.asyncio
async def test_check_prerequisites_returns_false_when_already_pending(
        db_session,
):
    comparison, generation_id = await create_comparison(db_session)

    await create_prerequisites(db_session)

    service = create_service(db_session)

    first_result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    second_result = await service.check_prerequisites_and_set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert first_result is True
    assert second_result is False
