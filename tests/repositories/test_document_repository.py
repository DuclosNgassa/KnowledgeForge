from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.repositories.document_repository import DocumentRepository


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def repository(mock_db):
    return DocumentRepository(mock_db)


@pytest.mark.asyncio
async def test_find_owned_document_ids_returns_all_owned_documents(
        repository,
        mock_db,
):
    user_id = uuid4()
    document_ids = [uuid4(), uuid4(), uuid4()]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = document_ids
    mock_db.execute.return_value = mock_result

    result = await repository.find_owned_document_ids(
        document_ids=document_ids,
        user_id=user_id,
    )

    assert result == set(document_ids)
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_owned_document_ids_returns_only_documents_owned_by_user(
        repository,
        mock_db,
):
    user_id = uuid4()
    document_ids = [uuid4(), uuid4(), uuid4()]
    owned_document_ids = [document_ids[0], document_ids[2]]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = owned_document_ids
    mock_db.execute.return_value = mock_result

    result = await repository.find_owned_document_ids(
        document_ids=document_ids,
        user_id=user_id,
    )

    assert result == {document_ids[0], document_ids[2]}


@pytest.mark.asyncio
async def test_find_owned_document_ids_returns_empty_set_when_no_documents_are_owned(
        repository,
        mock_db,
):
    user_id = uuid4()
    document_ids = [uuid4(), uuid4()]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = await repository.find_owned_document_ids(
        document_ids=document_ids,
        user_id=user_id,
    )

    assert result == set()
