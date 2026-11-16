from dataclasses import dataclass

import pytest

from app.services.summarization_batch_builder import (
    SummarizationBatchBuilder,
)


@dataclass
class FakeChunk:
    chunk_index: int
    content: str
    page_number: int | None = None


class FakeTokenCounter:

    def count(self, text: str) -> int:
        return int(text)

    def split_text(self, text: str, max_tokens: int) -> list[str]:
        value = int(text)

        segments = []
        while value > 0:
            segment = min(value, max_tokens)
            segments.append(str(segment))
            value -= segment

        return segments


@pytest.fixture
def builder():
    return SummarizationBatchBuilder(
        token_counter=FakeTokenCounter(),
        max_input_tokens=100,
    )


def test_builds_batches_within_token_limit(builder):
    chunks = [
        FakeChunk(0, "40"),
        FakeChunk(1, "30"),
        FakeChunk(2, "50"),
        FakeChunk(3, "20"),
    ]

    batches = builder.build(chunks)

    assert len(batches) == 2
    assert [c.chunk_index for c in batches[0].chunks] == [0, 1]
    assert batches[0].estimated_tokens == 70
    assert [c.chunk_index for c in batches[1].chunks] == [2, 3]
    assert batches[1].estimated_tokens == 70


def test_sorts_chunks_by_index(builder):
    chunks = [
        FakeChunk(2, "30"),
        FakeChunk(0, "30"),
        FakeChunk(1, "30"),
    ]

    batches = builder.build(chunks)

    assert [
               c.chunk_index
               for batch in batches
               for c in batch.chunks
           ] == [0, 1, 2]


def test_handles_empty_chunks(builder):
    assert builder.build([]) == []


def test_chunk_exactly_at_limit(builder):
    chunks = [FakeChunk(0, "100")]

    batches = builder.build(chunks)

    assert len(batches) == 1
    assert batches[0].estimated_tokens == 100


def test_splits_oversized_chunk(builder):
    chunks = [
        FakeChunk(0, "250"),
    ]

    batches = builder.build(chunks)

    assert len(batches) == 3

    assert [
               batch.estimated_tokens
               for batch in batches
           ] == [100, 100, 50]

    assert all(
        batch.estimated_tokens <= 100
        for batch in batches
    )


def test_preserves_metadata_when_splitting_oversized_chunk(builder):
    chunk = FakeChunk(
        chunk_index=0,
        content="150",
        page_number=5,
    )

    batches = builder.build([chunk])

    segments = [
        item
        for batch in batches
        for item in batch.chunks
    ]

    assert len(segments) == 2

    assert all(segment.chunk_index == 0 for segment in segments)
    assert all(segment.page_number == 5 for segment in segments)

    assert [segment.segment_index for segment in segments] == [0, 1]
