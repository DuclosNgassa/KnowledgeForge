import uuid
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.document_comparison import DocumentComparison
from app.models.enums import ComparisonStatus
from app.repositories.document_comparison_repository import (
    DocumentComparisonRepository,
)

USER_ID = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")

DOCUMENT_IDS = [
    UUID("f6554af6-04e4-4681-9698-569a0ef95cbf"),
    UUID("9463b82f-5b40-4a7c-9cab-6768d5e52776"),
]


async def create_comparison(db_session):
    repository = DocumentComparisonRepository(db_session)

    generation_id = uuid.uuid4()

    comparison = await repository.create_comparison(
        user_id=USER_ID,
        document_ids=DOCUMENT_IDS,
        title="Test comparison",
        criteria=["key_topics", "technologies"],
        generation_id=generation_id,
    )

    return comparison, generation_id


async def get_comparison_status(db_session, comparison_id):
    result = await db_session.execute(
        select(DocumentComparison.status).where(
            DocumentComparison.id == comparison_id
        )
    )

    return result.scalar_one()


@pytest.mark.asyncio
async def test_set_pending(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    updated = await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert updated is True

    status = await get_comparison_status(db_session, comparison.id)

    assert status == ComparisonStatus.PENDING


@pytest.mark.asyncio
async def test_set_pending_rejects_wrong_status(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    # First transition: WAITING_FOR_PREREQUISITES -> PENDING
    updated = await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert updated is True

    # Second transition should fail because status is already PENDING.
    updated = await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert updated is False

    status = await get_comparison_status(db_session, comparison.id)

    assert status == ComparisonStatus.PENDING


@pytest.mark.asyncio
async def test_claim_for_processing(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    claimed = await repository.claim_for_processing(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert claimed is not None
    assert claimed.id == comparison.id

    status = await get_comparison_status(db_session, comparison.id)

    assert status == ComparisonStatus.PROCESSING


@pytest.mark.asyncio
async def test_claim_for_processing_rejects_duplicate_claim(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    first_claim = await repository.claim_for_processing(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    second_claim = await repository.claim_for_processing(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert first_claim is not None
    assert second_claim is None


@pytest.mark.asyncio
async def test_set_completed(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    await repository.claim_for_processing(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    result_data = {
        "criterion_results": [
            {
                "criterion": "key_topics",
                "similarities": ["Artificial intelligence"],
                "differences": ["Different applications"],
                "document_insights": [],
            }
        ]
    }

    updated = await repository.set_completed(
        comparison_id=comparison.id,
        generation_id=generation_id,
        overview="Both documents discuss AI.",
        conclusion="The documents have related topics.",
        result_data=result_data,
    )

    assert updated is True

    result = await db_session.execute(
        select(
            DocumentComparison.status,
            DocumentComparison.overview,
            DocumentComparison.conclusion,
            DocumentComparison.result,
        ).where(DocumentComparison.id == comparison.id)
    )

    status, overview, conclusion, stored_result = result.one()

    assert status == ComparisonStatus.COMPLETED
    assert overview == "Both documents discuss AI."
    assert conclusion == "The documents have related topics."
    assert stored_result == result_data


@pytest.mark.asyncio
async def test_set_failed(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    await repository.claim_for_processing(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    error_message = "Comparison generation failed."

    updated = await repository.set_failed(
        comparison_id=comparison.id,
        generation_id=generation_id,
        error_message=error_message,
    )

    assert updated is True

    result = await db_session.execute(
        select(
            DocumentComparison.status,
            DocumentComparison.error_message,
        ).where(DocumentComparison.id == comparison.id)
    )

    status, stored_error = result.one()

    assert status == ComparisonStatus.FAILED
    assert stored_error == error_message


@pytest.mark.asyncio
async def test_set_dispatch_failed(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    error_message = "Taskiq dispatch failed."

    updated = await repository.set_dispatch_failed(
        comparison_id=comparison.id,
        generation_id=generation_id,
        error_message=error_message,
    )

    assert updated is True

    result = await db_session.execute(
        select(
            DocumentComparison.status,
            DocumentComparison.error_message,
        ).where(DocumentComparison.id == comparison.id)
    )

    status, stored_error = result.one()

    assert status == ComparisonStatus.FAILED
    assert stored_error == error_message


@pytest.mark.asyncio
async def test_status_transition_rejects_wrong_generation_id(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    wrong_generation_id = uuid.uuid4()

    updated = await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=wrong_generation_id,
    )

    assert updated is False

    status = await get_comparison_status(db_session, comparison.id)

    assert status == ComparisonStatus.WAITING_FOR_PREREQUISITES

    # The correct generation ID must still work.
    updated = await repository.set_pending(
        comparison_id=comparison.id,
        generation_id=generation_id,
    )

    assert updated is True


@pytest.mark.asyncio
async def test_claim_for_processing_accepts_pending_status(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison.id,
        generation_id,
    )

    claimed = await repository.claim_for_processing(
        comparison.id,
        generation_id,
    )

    assert claimed is not None
    assert claimed.status == ComparisonStatus.PROCESSING


@pytest.mark.asyncio
async def test_claim_for_processing_accepts_failed_status(db_session):
    comparison, generation_id = await create_comparison(db_session)

    repository = DocumentComparisonRepository(db_session)

    await repository.set_pending(
        comparison.id,
        generation_id,
    )

    await repository.claim_for_processing(
        comparison.id,
        generation_id,
    )

    await repository.set_failed(
        comparison.id,
        generation_id,
        "Temporary model error",
    )

    claimed = await repository.claim_for_processing(
        comparison.id,
        generation_id,
    )

    assert claimed is not None
    assert claimed.status == ComparisonStatus.PROCESSING
