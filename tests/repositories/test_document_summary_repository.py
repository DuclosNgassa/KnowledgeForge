import pytest
from uuid import UUID

from app.models.document_summary import DocumentSummary, SummaryStatus
from app.repositories.document_summary_repository import DocumentSummaryRepository

DOCUMENT_IDS = [
    UUID("0aa84078-f7b2-435f-8920-7da348507bd8"),
    UUID("952baad5-154a-479d-b21a-d6b484b4ae8c"),
    UUID("41977992-589b-49ff-a284-68bbeb40da0d"),
]


async def create_summary(db_session, document_id, status):
    summary = DocumentSummary(
        document_id=document_id,
        status=status,
    )
    db_session.add(summary)
    await db_session.flush()
    return summary


@pytest.mark.asyncio
async def test_find_completed_document_ids_returns_all_completed(db_session):
    for document_id in DOCUMENT_IDS:
        await create_summary(
            db_session,
            document_id,
            SummaryStatus.COMPLETED,
        )

    repository = DocumentSummaryRepository(db_session)

    result = await repository.find_completed_document_ids(DOCUMENT_IDS)

    assert result == set(DOCUMENT_IDS)


@pytest.mark.asyncio
async def test_find_completed_document_ids_returns_only_completed(db_session):
    await create_summary(
        db_session,
        DOCUMENT_IDS[0],
        SummaryStatus.COMPLETED,
    )
    await create_summary(
        db_session,
        DOCUMENT_IDS[1],
        SummaryStatus.PROCESSING,
    )
    await create_summary(
        db_session,
        DOCUMENT_IDS[2],
        SummaryStatus.FAILED,
    )

    repository = DocumentSummaryRepository(db_session)

    result = await repository.find_completed_document_ids(DOCUMENT_IDS)

    assert result == {DOCUMENT_IDS[0]}


@pytest.mark.asyncio
async def test_find_completed_document_ids_returns_empty_set(db_session):
    await create_summary(
        db_session,
        DOCUMENT_IDS[0],
        SummaryStatus.PENDING,
    )

    repository = DocumentSummaryRepository(db_session)

    result = await repository.find_completed_document_ids(DOCUMENT_IDS)

    assert result == set()


@pytest.mark.asyncio
async def test_find_completed_document_ids_with_empty_list(db_session):
    repository = DocumentSummaryRepository(db_session)

    result = await repository.find_completed_document_ids([])

    assert result == set()
