from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate

from app.services.token_counter import TokenCounter


@dataclass(frozen=True)
class SummarizationChunkSegment:
    chunk_index: int
    segment_index: int
    page_number: int | None
    content: str


@dataclass(frozen=True)
class SummarizationBatch:
    chunks: list
    estimated_tokens: int


def format_chunk_sections(chunks: Sequence) -> str:
    sections = []

    for chunk in chunks:
        page_info = (
            f", page {chunk.page_number}"
            if chunk.page_number is not None
            else ""
        )

        segment_info = (
            f", segment {chunk.segment_index}"
            if hasattr(chunk, "segment_index")
            else ""
        )

        sections.append(
            f"[Chunk {chunk.chunk_index}"
            f"{page_info}{segment_info}]\n"
            f"{chunk.content}"
        )

    return "\n\n".join(sections)


class SummarizationBatchBuilder:

    def __init__(
            self,
            token_counter: TokenCounter,
            prompt: ChatPromptTemplate,
            max_input_tokens: int = 6_000,
    ):
        self.token_counter = token_counter
        self.prompt = prompt
        self.max_input_tokens = max_input_tokens

        empty_messages = self.prompt.format_messages(text="")

        self.empty_prompt_tokens = (
            self.token_counter.count_messages(empty_messages)
        )

        if self.empty_prompt_tokens >= self.max_input_tokens:
            raise ValueError(
                "MAP prompt instructions already exceed the token budget."
            )

    def build(self, chunks: list) -> list[SummarizationBatch]:
        batches = []
        current_chunks = []

        sorted_chunks = sorted(
            chunks,
            key=lambda item: item.chunk_index,
        )

        for chunk in sorted_chunks:
            if self._estimate_tokens([chunk]) > self.max_input_tokens:
                segments = self._split_chunk(chunk)
            else:
                segments = [chunk]

            for segment in segments:
                candidate = current_chunks + [segment]

                if (
                        current_chunks
                        and self._estimate_tokens(candidate)
                        > self.max_input_tokens
                ):
                    batches.append(self._create_batch(current_chunks))
                    current_chunks = []

                current_chunks.append(segment)

        if current_chunks:
            batches.append(self._create_batch(current_chunks))

        return batches

    def _estimate_tokens(self, chunks: Sequence) -> int:
        text = format_chunk_sections(chunks)

        messages = self.prompt.format_messages(
            text=text,
        )

        return self.token_counter.count_messages(messages)

    def _create_batch(
            self,
            chunks: list,
    ) -> SummarizationBatch:
        return SummarizationBatch(
            chunks=chunks,
            estimated_tokens=self._estimate_tokens(chunks),
        )

    def _split_chunk(self, chunk) -> list[SummarizationChunkSegment]:
        content_budget = (
                self.max_input_tokens - self.empty_prompt_tokens
        )

        while content_budget > 0:
            text_segments = self.token_counter.split_text(
                chunk.content,
                content_budget,
            )

            segments = [
                SummarizationChunkSegment(
                    chunk_index=chunk.chunk_index,
                    segment_index=index,
                    page_number=chunk.page_number,
                    content=content,
                )
                for index, content in enumerate(text_segments)
            ]

            oversized_segments = [
                segment
                for segment in segments
                if self._estimate_tokens([segment])
                   > self.max_input_tokens
            ]

            if not oversized_segments:
                return segments

            largest_overage = max(
                self._estimate_tokens([segment])
                - self.max_input_tokens
                for segment in oversized_segments
            )

            content_budget -= max(largest_overage, 8)

        raise ValueError(
            f"Unable to split chunk {chunk.chunk_index} "
            "within the MAP token budget."
        )
