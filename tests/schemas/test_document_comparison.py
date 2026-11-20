from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.document_comparison import (
    ComparisonCriterion,
    CreateDocumentComparisonRequest,
)


def test_create_comparison_request_with_default_criteria():
    document_ids = [uuid4(), uuid4()]

    request = CreateDocumentComparisonRequest(
        document_ids=document_ids,
    )

    assert request.document_ids == document_ids
    assert request.criteria == [
        ComparisonCriterion.KEY_TOPICS,
        ComparisonCriterion.TECHNOLOGIES,
        ComparisonCriterion.NAMED_ENTITIES,
    ]
    assert request.title is None


def test_create_comparison_request_with_custom_title():
    request = CreateDocumentComparisonRequest(
        document_ids=[uuid4(), uuid4()],
        title="Technology Comparison",
    )

    assert request.title == "Technology Comparison"


def test_create_comparison_request_with_single_criterion():
    request = CreateDocumentComparisonRequest(
        document_ids=[uuid4(), uuid4()],
        criteria=[ComparisonCriterion.TECHNOLOGIES],
    )

    assert request.criteria == [ComparisonCriterion.TECHNOLOGIES]


def test_create_comparison_request_with_multiple_criteria():
    criteria = [
        ComparisonCriterion.KEY_TOPICS,
        ComparisonCriterion.TECHNOLOGIES,
    ]

    request = CreateDocumentComparisonRequest(
        document_ids=[uuid4(), uuid4()],
        criteria=criteria,
    )

    assert request.criteria == criteria


def test_create_comparison_request_rejects_duplicate_document_ids():
    document_id = uuid4()

    with pytest.raises(
            ValidationError,
            match="Document IDs must be unique",
    ):
        CreateDocumentComparisonRequest(
            document_ids=[document_id, document_id],
        )


def test_create_comparison_request_rejects_duplicate_criteria():
    with pytest.raises(
            ValidationError,
            match="Comparison criteria must be unique",
    ):
        CreateDocumentComparisonRequest(
            document_ids=[uuid4(), uuid4()],
            criteria=[
                ComparisonCriterion.KEY_TOPICS,
                ComparisonCriterion.KEY_TOPICS,
            ],
        )


def test_create_comparison_request_requires_at_least_two_documents():
    with pytest.raises(ValidationError):
        CreateDocumentComparisonRequest(
            document_ids=[uuid4()],
        )


def test_create_comparison_request_requires_at_least_one_criterion():
    with pytest.raises(ValidationError):
        CreateDocumentComparisonRequest(
            document_ids=[uuid4(), uuid4()],
            criteria=[],
        )


def test_create_comparison_request_rejects_invalid_criterion():
    with pytest.raises(ValidationError):
        CreateDocumentComparisonRequest(
            document_ids=[uuid4(), uuid4()],
            criteria=["invalid_criterion"],
        )
