import uuid

import pytest
from pyarrow.lib import UUID

from app.models import DocumentExtraction, DocumentSummary, DocumentComparison
from app.models.enums import ComparisonStatus, ExtractionStatus, SummaryStatus
from app.repositories.document_comparison_repository import (
    DocumentComparisonRepository,
)

TEST_USER_ID = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")
DOCUMENT_IDS = [UUID("952baad5-154a-479d-b21a-d6b484b4ae8c"), UUID("411dab15-d046-4d9f-a511-ab0d5451da27")]


async def create_comparison(db_session):
    repository = DocumentComparisonRepository(db_session)

    generation_id = uuid.uuid4()

    comparison = await repository.create_comparison(
        user_id=TEST_USER_ID,
        document_ids=DOCUMENT_IDS,
        title="Test comparison",
        criteria=["key_topics", "technologies"],
        generation_id=generation_id,
    )

    return comparison, generation_id


async def create_comparison_inputs(
        db_session,
        document_id,
        summary_status=SummaryStatus.COMPLETED,
        extraction_status=ExtractionStatus.COMPLETED,
):
    summary = DocumentSummary(
        document_id=document_id,
        status=summary_status,
        content=f"Summary for {document_id}",
    )

    extraction = DocumentExtraction(
        document_id=document_id,
        status=extraction_status,
        extraction_data={
            "document_category": "Technical report",
            "key_topics": ["AI", "Machine Learning"],
            "named_entities": [],
            "technologies": ["Python", "FastAPI"],
            "important_dates": [],
        },
    )

    db_session.add_all([summary, extraction])
    await db_session.flush()


@pytest.mark.asyncio
async def test_create_comparison(db_session):
    user_id = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")
    document_ids = [UUID("f6554af6-04e4-4681-9698-569a0ef95cbf"), UUID("9463b82f-5b40-4a7c-9cab-6768d5e52776")]

    repository = DocumentComparisonRepository(db_session)

    comparison = await repository.create_comparison(
        user_id=UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e"),
        document_ids=document_ids,
        title="Technology comparison",
        criteria=["technologies", "key_topics"],
        generation_id=uuid.uuid4(),
    )

    assert comparison.id is not None
    assert comparison.user_id == user_id
    assert comparison.title == "Technology comparison"
    assert comparison.criteria == ["technologies", "key_topics"]
    assert comparison.status == ComparisonStatus.WAITING_FOR_PREREQUISITES
    assert len(comparison.items) == 2


@pytest.mark.asyncio
async def test_create_comparison_preserves_document_order(db_session):
    user_id = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")
    document_ids = [UUID("f6554af6-04e4-4681-9698-569a0ef95cbf"), UUID("9463b82f-5b40-4a7c-9cab-6768d5e52776"),
                    UUID("4a119dc8-1bb0-479f-8f51-68884a57b616")]

    repository = DocumentComparisonRepository(db_session)

    comparison = await repository.create_comparison(
        user_id=user_id,
        document_ids=document_ids,
        title=None,
        criteria=["key_topics"],
        generation_id=uuid.uuid4(),
    )

    items = sorted(comparison.items, key=lambda item: item.position)

    assert [item.document_id for item in items] == document_ids
    assert [item.position for item in items] == [0, 1, 2]


@pytest.mark.asyncio
async def test_find_by_id_returns_comparison(db_session):
    user_id = UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e")

    repository = DocumentComparisonRepository(db_session)

    created = await repository.create_comparison(
        user_id=user_id,
        document_ids=[UUID("f6554af6-04e4-4681-9698-569a0ef95cbf"), UUID("411dab15-d046-4d9f-a511-ab0d5451da27")],
        title="Test comparison",
        criteria=["key_topics"],
        generation_id=uuid.uuid4(),
    )

    await db_session.commit()

    found = await repository.find_by_id(
        comparison_id=created.id,
        user_id=user_id,
    )

    assert found is not None
    assert found.id == created.id
    assert len(found.items) == 2


@pytest.mark.asyncio
async def test_find_by_id_returns_none_for_other_user(db_session):
    repository = DocumentComparisonRepository(db_session)
    created = await repository.create_comparison(
        user_id=UUID("c1271fdd-8096-4a49-8a9d-5f551cac576e"),
        document_ids=[UUID("f6554af6-04e4-4681-9698-569a0ef95cbf"), UUID("9463b82f-5b40-4a7c-9cab-6768d5e52776")],
        title=None,
        criteria=["key_topics"],
        generation_id=uuid.uuid4(),
    )

    await db_session.commit()

    found = await repository.find_by_id(
        comparison_id=created.id,
        user_id=uuid.uuid4(),
    )

    assert found is None


@pytest.mark.asyncio
async def test_find_comparison_inputs_returns_all_documents(db_session):
    comparison, _ = await create_comparison(db_session)

    for document_id in DOCUMENT_IDS:
        await create_comparison_inputs(
            db_session,
            document_id,
        )

    repository = DocumentComparisonRepository(db_session)

    result = await repository.find_comparison_inputs(comparison.id)

    assert len(result) == 2

    for item in result:
        assert item["document_id"] in DOCUMENT_IDS
        assert item["summary"] is not None
        assert item["extraction"] is not None
        assert item["extraction"]["document_category"] == "Technical report"
        assert item["extraction"]["key_topics"] == [
            "AI",
            "Machine Learning",
        ]


@pytest.mark.asyncio
async def test_find_comparison_inputs_preserves_document_order(db_session):
    comparison, _ = await create_comparison(db_session)

    for document_id in DOCUMENT_IDS:
        await create_comparison_inputs(
            db_session,
            document_id,
        )

    repository = DocumentComparisonRepository(db_session)

    result = await repository.find_comparison_inputs(comparison.id)

    result_document_ids = [
        item["document_id"]
        for item in result
    ]

    assert result_document_ids == DOCUMENT_IDS


@pytest.mark.asyncio
async def test_find_comparison_inputs_returns_none_for_incomplete_prerequisites(
        db_session,
):
    comparison, _ = await create_comparison(db_session)

    await create_comparison_inputs(
        db_session,
        DOCUMENT_IDS[0],
        summary_status=SummaryStatus.PROCESSING,
        extraction_status=ExtractionStatus.COMPLETED,
    )

    await create_comparison_inputs(
        db_session,
        DOCUMENT_IDS[1],
        summary_status=SummaryStatus.COMPLETED,
        extraction_status=ExtractionStatus.FAILED,
    )

    repository = DocumentComparisonRepository(db_session)

    result = await repository.find_comparison_inputs(comparison.id)

    assert len(result) == 2

    first_document = result[0]
    second_document = result[1]

    assert first_document["document_id"] == DOCUMENT_IDS[0]
    assert first_document["summary"] is None
    assert first_document["extraction"] is not None

    assert second_document["document_id"] == DOCUMENT_IDS[1]
    assert second_document["summary"] is not None
    assert second_document["extraction"] is None


@pytest.mark.asyncio
async def test_find_comparison_inputs_returns_empty_list_for_no_items(
        db_session,
):
    repository = DocumentComparisonRepository(db_session)

    comparison = DocumentComparison(
        user_id=TEST_USER_ID,
        title="Empty comparison",
        criteria=["key_topics"],
        status=ComparisonStatus.WAITING_FOR_PREREQUISITES,
        generation_id=uuid.uuid4(),
    )

    db_session.add(comparison)
    await db_session.flush()

    result = await repository.find_comparison_inputs(comparison.id)

    assert result == []
