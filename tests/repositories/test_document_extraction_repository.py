import pytest
from uuid import UUID

from app.models.document_extraction import (
    DocumentExtraction,
    ExtractionStatus,
)
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)

DOCUMENT_IDS = [
    UUID("0aa84078-f7b2-435f-8920-7da348507bd8"),
    UUID("952baad5-154a-479d-b21a-d6b484b4ae8c"),
    UUID("41977992-589b-49ff-a284-68bbeb40da0d"),
]


async def create_extraction(db_session, document_id, status):
    extraction = DocumentExtraction(
        document_id=document_id,
        status=status,
    )
    db_session.add(extraction)
    await db_session.flush()
    return extraction


@pytest.mark.asyncio
async def test_find_completed_document_ids_returns_all_completed(db_session):
    for document_id in DOCUMENT_IDS:
        await create_extraction(
            db_session,
            document_id,
            ExtractionStatus.COMPLETED,
        )

    repository = DocumentExtractionRepository(db_session)

    result = await repository.find_completed_document_ids(DOCUMENT_IDS)

    assert result == set(DOCUMENT_IDS)


@pytest.mark.asyncio
async def test_find_completed_document_ids_returns_only_completed(db_session):
    await create_extraction(
        db_session,
        DOCUMENT_IDS[0],
        ExtractionStatus.COMPLETED,
    )
    await create_extraction(
        db_session,
        DOCUMENT_IDS[1],
        ExtractionStatus.PROCESSING,
    )
    await create_extraction(
        db_session,
        DOCUMENT_IDS[2],
        ExtractionStatus.FAILED,
    )

    repository = DocumentExtractionRepository(db_session)

    result = await repository.find_completed_document_ids(DOCUMENT_IDS)

    assert result == {DOCUMENT_IDS[0]}


@pytest.mark.asyncio
async def test_find_completed_document_ids_returns_empty_set(db_session):
    await create_extraction(
        db_session,
        DOCUMENT_IDS[0],
        ExtractionStatus.PENDING,
    )

    repository = DocumentExtractionRepository(db_session)

    result = await repository.find_completed_document_ids(DOCUMENT_IDS)

    assert result == set()


@pytest.mark.asyncio
async def test_find_completed_document_ids_with_empty_list(db_session):
    repository = DocumentExtractionRepository(db_session)

    result = await repository.find_completed_document_ids([])

    assert result == set()
