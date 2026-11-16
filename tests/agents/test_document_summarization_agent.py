import asyncio

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from langchain_core.prompts import ChatPromptTemplate

from app.agents.document_summarization_agent import DocumentSummarizationAgent
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
        return len(text)

    def count_messages(self, messages) -> int:
        return sum(
            self.count(message.content)
            for message in messages
            if isinstance(message.content, str)
        )

    def split_text(
            self,
            text: str,
            max_tokens: int,
    ) -> list[str]:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")

        return [
            text[i:i + max_tokens]
            for i in range(0, len(text), max_tokens)
        ]


def make_response(content: str):
    return MagicMock(content=content)


def configure_map_budget(agent, budget: int):
    agent.MAP_INPUT_TOKEN_BUDGET = budget

    agent.batch_builder = SummarizationBatchBuilder(
        token_counter=agent.token_counter,
        prompt=agent.map_prompt,
        max_input_tokens=budget,
    )


def configure_one_chunk_per_batch(agent, chunks):
    single_chunk_tokens = agent.batch_builder._estimate_tokens(
        [chunks[0]]
    )

    two_chunk_tokens = agent.batch_builder._estimate_tokens(
        chunks[:2]
    )

    assert single_chunk_tokens < two_chunk_tokens

    configure_map_budget(
        agent,
        two_chunk_tokens - 1,
    )


@pytest.fixture
def agent():
    model = MagicMock()

    instance = DocumentSummarizationAgent(model=model)

    instance.token_counter = FakeTokenCounter()

    instance.map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize."),
        ("human", "Sections:\n\n{text}"),
    ])

    instance.MAP_INPUT_TOKEN_BUDGET = 100
    instance.REDUCE_INPUT_TOKEN_BUDGET = 100
    instance.FINAL_INPUT_TOKEN_BUDGET = 100

    instance.batch_builder = SummarizationBatchBuilder(
        token_counter=instance.token_counter,
        prompt=instance.map_prompt,
        max_input_tokens=100,
    )

    # Track concurrent MAP requests.
    execution_state = {
        "active": 0,
        "max_active": 0,
    }

    async def map_side_effect(messages):
        execution_state["active"] += 1

        execution_state["max_active"] = max(
            execution_state["max_active"],
            execution_state["active"],
        )

        try:
            text = messages[1].content

            await asyncio.sleep(0)

            return make_response(f"map-{text}")

        finally:
            execution_state["active"] -= 1

    model.ainvoke = AsyncMock(
        side_effect=map_side_effect
    )

    instance.execution_state = execution_state

    instance.reduce_chain = MagicMock()
    instance.reduce_chain.ainvoke = AsyncMock(
        side_effect=lambda inputs: make_response(
            f"reduce-{inputs['summaries']}"
        )
    )

    instance.final_chain = MagicMock()
    instance.final_chain.ainvoke = AsyncMock(
        return_value=make_response("Final document summary")
    )

    return instance


@pytest.mark.asyncio
async def test_rejects_empty_document(agent):
    with pytest.raises(ValueError, match="empty document"):
        await agent.summarize([])


@pytest.mark.asyncio
async def test_summarizes_single_batch(agent):
    chunks = [
        FakeChunk(chunk_index=0, content="short"),
    ]

    result = await agent.summarize(chunks)

    assert result == "Final document summary"

    agent.model.ainvoke.assert_awaited_once()
    agent.reduce_chain.ainvoke.assert_not_awaited()
    agent.final_chain.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_processes_map_batches_sequentially(agent):
    chunks = [
        FakeChunk(chunk_index=0, content="123456"),
        FakeChunk(chunk_index=1, content="abcdef"),
        FakeChunk(chunk_index=2, content="uvwxyz"),
    ]

    configure_one_chunk_per_batch(agent, chunks)

    result = await agent.summarize(chunks)

    assert result == "Final document summary"

    assert agent.model.ainvoke.await_count == 3

    expected_sections = [
        "[Chunk 0]\n123456",
        "[Chunk 1]\nabcdef",
        "[Chunk 2]\nuvwxyz",
    ]

    actual_calls = agent.model.ainvoke.await_args_list

    for actual_call, expected_section in zip(
            actual_calls,
            expected_sections,
    ):
        messages = actual_call.args[0]

        assert messages[1].content == (
            f"Sections:\n\n{expected_section}"
        )

    # Verify actual sequential execution.
    assert agent.execution_state["max_active"] == 1

    agent.reduce_chain.ainvoke.assert_not_awaited()
    agent.final_chain.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_splits_oversized_chunk(agent):
    original_content = "abcdefghijklmnopqrstu"

    chunks = [
        FakeChunk(
            chunk_index=0,
            content=original_content,
        ),
    ]

    # Allow enough room for segment metadata and content,
    # but not enough for the original chunk.
    budget = agent.batch_builder.empty_prompt_tokens + 30

    configure_map_budget(agent, budget)

    batches = agent.batch_builder.build(chunks)

    segments = [
        segment
        for batch in batches
        for segment in batch.chunks
    ]

    # The original chunk must be split.
    assert len(segments) > 1

    # Preserve all original content and ordering.
    assert "".join(
        segment.content for segment in segments
    ) == original_content

    # Segment indices must be sequential.
    assert [
               segment.segment_index for segment in segments
           ] == list(range(len(segments)))

    # Every complete MAP request must respect the budget.
    for batch in batches:
        assert batch.estimated_tokens <= budget

    agent._recursive_reduce = AsyncMock(
        side_effect=lambda summaries: summaries
    )

    await agent.summarize(chunks)

    assert agent.model.ainvoke.await_count == len(batches)
    agent._recursive_reduce.assert_awaited_once()


@pytest.mark.asyncio
async def test_generates_final_summary(agent):
    chunks = [
        FakeChunk(
            chunk_index=0,
            content="small document",
        ),
    ]

    await agent.summarize(chunks)

    final_input = agent.final_chain.ainvoke.await_args.args[0]

    assert "summaries" in final_input
    assert "map-" in final_input["summaries"]


@pytest.mark.asyncio
async def test_recursively_reduces_summaries(agent):
    chunks = [
        FakeChunk(chunk_index=i, content="123456")
        for i in range(4)
    ]

    configure_one_chunk_per_batch(agent, chunks)

    agent.REDUCE_INPUT_TOKEN_BUDGET = 2
    agent.FINAL_INPUT_TOKEN_BUDGET = 1

    agent.model.ainvoke = AsyncMock(
        side_effect=[
            make_response("A"),
            make_response("B"),
            make_response("C"),
            make_response("D"),
        ]
    )

    agent.reduce_chain.ainvoke = AsyncMock(
        return_value=make_response("R")
    )

    result = await agent.summarize(chunks)

    assert result == "Final document summary"

    # First reduction round: two batches.
    # Second reduction round: one batch.
    assert agent.reduce_chain.ainvoke.await_count == 3

    agent.final_chain.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_preserves_single_summary_batches(agent):
    agent.REDUCE_INPUT_TOKEN_BUDGET = 2
    agent.FINAL_INPUT_TOKEN_BUDGET = 1

    agent.reduce_chain.ainvoke = AsyncMock(
        return_value=make_response("R")
    )

    result = await agent._recursive_reduce(
        ["A", "B", "C"]
    )

    assert result == ["R"]

    # First round: ["A", "B"] and ["C"].
    # Second round: ["R", "C"].
    assert agent.reduce_chain.ainvoke.await_count == 2
