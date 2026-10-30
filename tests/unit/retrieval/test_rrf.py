from uuid import uuid4

from app.schemas.search_result import SearchResult
from app.services.search_service import _reciprocal_rank_fusion


def make_result(chunk_id):
    return SearchResult(
        chunk_id=chunk_id,
        document_id=uuid4(),
        content=f"Content {chunk_id}",
        source="upload",
        file_name="document.pdf",
        page_number=1,
        score=0.9,
    )


def test_rrf_returns_unique_chunks():
    chunk_a = uuid4()
    chunk_b = uuid4()

    results = _reciprocal_rank_fusion(
        [
            [make_result(chunk_a), make_result(chunk_b)],
            [make_result(chunk_a)],
        ]
    )

    assert len(results) == 2
    assert len({result.chunk_id for result in results}) == 2


def test_rrf_accumulates_scores():
    chunk_a = uuid4()
    chunk_b = uuid4()

    results = _reciprocal_rank_fusion(
        [
            [make_result(chunk_a), make_result(chunk_b)],
            [make_result(chunk_b), make_result(chunk_a)],
        ]
    )

    # Both chunks have identical accumulated RRF scores.
    assert len(results) == 2


def test_rrf_returns_empty_for_empty_lists():
    assert _reciprocal_rank_fusion([]) == []

    assert _reciprocal_rank_fusion([[], []]) == []
