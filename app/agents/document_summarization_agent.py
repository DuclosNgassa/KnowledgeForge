import time
from collections.abc import Sequence
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from app.models.document_chunk import DocumentChunk
from app.observability.logging import logger
from app.services.summarization_batch_builder import SummarizationBatchBuilder, format_chunk_sections
from app.services.token_counter import TokenCounter


class DocumentSummarizationAgent:
    MAP_INPUT_TOKEN_BUDGET = 6_000
    REDUCE_INPUT_TOKEN_BUDGET = 6_000
    FINAL_INPUT_TOKEN_BUDGET = 6_000

    def __init__(self, model: BaseChatModel):
        self.model = model

        self.token_counter = TokenCounter()

        self.map_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are a document analysis assistant.

                Summarize the supplied document sections.

                Requirements:
                - Identify the main topics and important ideas.
                - Preserve relevant facts, technical details, and conclusions.
                - Retain important names, dates, numbers, and terminology.
                - Do not introduce information that is not in the source.
                - Remove repetition.
                - Produce a concise, self-contained summary.
                - Preserve the original order of the sections.
                - Aim for no more than 150 words.
                """
            ),
            (
                "human",
                "Document sections:\n\n{text}",
            ),
        ])

        self.batch_builder = SummarizationBatchBuilder(
            token_counter=self.token_counter,
            max_input_tokens=self.MAP_INPUT_TOKEN_BUDGET,
            prompt=self.map_prompt,
        )

        self.reduce_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an expert document summarization assistant.

                Combine the supplied intermediate summaries into one
                coherent summary.

                Requirements:
                - Preserve the most important facts and ideas.
                - Retain relevant technical details, names, dates,
                  numbers, and conclusions.
                - Remove repetition and redundant information.
                - Preserve logical relationships between topics.
                - Do not introduce unsupported information.
                - If sources contain conflicting statements, preserve
                  the distinction.
                - Aim for no more than 200 words.
                """
            ),
            (
                "human",
                "Intermediate summaries:\n\n{summaries}",
            ),
        ])

        self.reduce_chain = self.reduce_prompt | self.model

        self.final_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an expert document summarization assistant.

                Produce a comprehensive summary of the original document
                using the supplied intermediate summaries.

                Requirements:
                - Write approximately 4-6 paragraphs.
                - Explain the document's main subject and purpose.
                - Cover its most important concepts, findings, and
                  conclusions.
                - Preserve important technical details.
                - Remove repetition.
                - Maintain a coherent logical flow.
                - Do not introduce information that is not supported
                  by the supplied summaries.
                - Do not mention that the text was summarized in stages.
                """
            ),
            (
                "human",
                "Document summaries:\n\n{summaries}",
            ),
        ])

        self.final_chain = self.final_prompt | self.model

    async def summarize(
            self,
            chunks: Sequence[DocumentChunk],
    ) -> str:

        if not chunks:
            raise ValueError("Cannot summarize an empty document")

        start_time = time.perf_counter()

        ordered_chunks = sorted(
            chunks,
            key=lambda chunk: chunk.chunk_index,
        )

        source_tokens = sum(
            self.token_counter.count(chunk.content)
            for chunk in ordered_chunks
        )

        # Step 1: Build token-based batches.
        batches = self.batch_builder.build(list(ordered_chunks))

        logger.info(
            "Starting document summarization: "
            "chunks=%d, source_tokens=%d, map_batches=%d",
            len(ordered_chunks),
            source_tokens,
            len(batches),
        )

        # Step 2: MAP - sequential processing.
        map_results = []

        map_start = time.perf_counter()

        for index, batch in enumerate(batches, start=1):
            batch_start = time.perf_counter()

            result = await self._invoke_map(batch.chunks)
            map_results.append(result)

            logger.info(
                "Map batch %d/%d completed: "
                "input_tokens=%d, duration=%.2fs",
                index,
                len(batches),
                batch.estimated_tokens,
                time.perf_counter() - batch_start,
            )

        logger.info(
            "Map stage completed: batches=%d, duration=%.2fs",
            len(batches),
            time.perf_counter() - map_start,
        )

        # Step 3: REDUCE.
        reduce_start = time.perf_counter()

        reduced_summaries = await self._recursive_reduce(map_results)

        logger.info(
            "Reduce stage completed: "
            "initial_summaries=%d, final_summaries=%d, duration=%.2fs",
            len(map_results),
            len(reduced_summaries),
            time.perf_counter() - reduce_start,
        )

        # Step 4: FINAL.
        final_input = "\n\n".join(reduced_summaries)

        final_messages = self.final_prompt.format_messages(
            summaries=final_input,
        )

        final_input_tokens = self.token_counter.count_messages(
            final_messages
        )

        if final_input_tokens > self.FINAL_INPUT_TOKEN_BUDGET:
            raise ValueError(
                "FINAL prompt exceeds token budget: "
                f"{final_input_tokens} > {self.FINAL_INPUT_TOKEN_BUDGET}"
            )

        final_start = time.perf_counter()

        result = await self.final_chain.ainvoke({
            "summaries": final_input,
        })

        summary = self._extract_text(result.content)

        if not summary:
            raise ValueError("FINAL model returned an empty summary.")

        logger.info(
            "Final summary generated: "
            "input_tokens=%d, output_tokens=%d, duration=%.2fs",
            final_input_tokens,
            self.token_counter.count(summary),
            time.perf_counter() - final_start,
        )

        logger.info(
            "Document summarization completed: total_duration=%.2fs",
            time.perf_counter() - start_time,
        )

        return summary

    async def _invoke_map(self, chunks: Sequence) -> str:
        messages = self.map_prompt.format_messages(
            text=format_chunk_sections(chunks),
        )

        estimated_tokens = self.token_counter.count_messages(messages)

        if estimated_tokens > self.MAP_INPUT_TOKEN_BUDGET:
            raise ValueError(
                "MAP prompt exceeds token budget: "
                f"{estimated_tokens} > {self.MAP_INPUT_TOKEN_BUDGET}"
            )

        result = await self.model.ainvoke(messages)

        return self._extract_text(result.content)

    async def _recursive_reduce(
            self,
            summaries: list[str],
    ) -> list[str]:

        if not summaries:
            raise ValueError("Cannot reduce an empty list of summaries.")

        current = self._prepare_summaries_for_reduction(summaries)
        round_number = 0

        while self._estimate_prompt_tokens(
                self.final_prompt,
                summaries="\n\n".join(current),
        ) > self.FINAL_INPUT_TOKEN_BUDGET:

            round_number += 1
            round_start = time.perf_counter()

            batches = self._group_texts_by_tokens(
                current,
                self.REDUCE_INPUT_TOKEN_BUDGET,
            )

            logger.info(
                "Reduction round %d started: "
                "summaries=%d, input_tokens=%d, batches=%d",
                round_number,
                len(current),
                self._total_tokens(current),
                len(batches),
            )

            if not any(len(batch) >= 2 for batch in batches):
                raise ValueError(
                    "Unable to reduce summaries within the configured "
                    "token budget. No batch contains multiple summaries."
                )

            reduced = []

            for batch in batches:
                if len(batch) == 1:
                    reduced.append(batch[0])
                else:
                    result = await self._invoke_reduce(batch)
                    reduced.append(result)

            if len(reduced) >= len(current):
                raise RuntimeError(
                    "Recursive summarization did not reduce "
                    "the number of summaries."
                )

            current = self._prepare_summaries_for_reduction(reduced)

            logger.info(
                "Reduction round %d completed: "
                "output_summaries=%d, output_tokens=%d, duration=%.2fs",
                round_number,
                len(current),
                self._total_tokens(current),
                time.perf_counter() - round_start,
            )

        return current

    def _group_texts_by_tokens(
            self,
            texts: Sequence[str],
            max_tokens: int,
    ) -> list[list[str]]:

        batches: list[list[str]] = []
        current_batch: list[str] = []

        for text in texts:
            candidate_batch = [*current_batch, text]

            candidate_input = "\n\n".join(candidate_batch)

            candidate_tokens = self._estimate_prompt_tokens(
                self.reduce_prompt,
                summaries=candidate_input,
            )

            if candidate_tokens > max_tokens:
                if not current_batch:
                    raise ValueError(
                        "A single summary exceeds the REDUCE prompt "
                        f"budget ({candidate_tokens} > {max_tokens})."
                    )

                batches.append(current_batch)
                current_batch = [text]

                single_input = text

                single_tokens = self._estimate_prompt_tokens(
                    self.reduce_prompt,
                    summaries=single_input,
                )

                if single_tokens > max_tokens:
                    raise ValueError(
                        "A single summary exceeds the REDUCE prompt "
                        f"budget ({single_tokens} > {max_tokens})."
                    )
            else:
                current_batch = candidate_batch

        if current_batch:
            batches.append(current_batch)

        return batches

    def _total_tokens(self, texts: Sequence[str]) -> int:
        return sum(
            self.token_counter.count(text)
            for text in texts
        )

    async def _invoke_reduce(
            self,
            summaries: Sequence[str],
    ) -> str:

        input_text = "\n\n".join(summaries)

        messages = self.reduce_prompt.format_messages(
            summaries=input_text,
        )

        input_tokens = self.token_counter.count_messages(messages)

        if input_tokens > self.REDUCE_INPUT_TOKEN_BUDGET:
            raise ValueError(
                "REDUCE prompt exceeds token budget: "
                f"{input_tokens} > {self.REDUCE_INPUT_TOKEN_BUDGET}"
            )

        start_time = time.perf_counter()

        result = await self.reduce_chain.ainvoke({
            "summaries": input_text,
        })

        output = self._extract_text(result.content)

        if not output:
            raise ValueError("REDUCE model returned an empty summary.")

        logger.info(
            "Reduce batch completed: "
            "input_tokens=%d, output_tokens=%d, duration=%.2fs",
            input_tokens,
            self.token_counter.count(output),
            time.perf_counter() - start_time,
        )

        return output

    def _estimate_prompt_tokens(
            self,
            prompt: ChatPromptTemplate,
            **kwargs,
    ) -> int:
        messages = prompt.format_messages(**kwargs)

        return self.token_counter.count_messages(messages)

    def _split_summary_to_fit_budgets(
            self,
            summary: str,
    ) -> list[str]:

        reduce_empty_tokens = self._estimate_prompt_tokens(
            self.reduce_prompt,
            summaries="",
        )

        final_empty_tokens = self._estimate_prompt_tokens(
            self.final_prompt,
            summaries="",
        )

        content_budget = min(
            self.REDUCE_INPUT_TOKEN_BUDGET - reduce_empty_tokens,
            self.FINAL_INPUT_TOKEN_BUDGET - final_empty_tokens,
        )

        if content_budget <= 0:
            raise ValueError(
                "REDUCE or FINAL token budget is too small "
                "to accommodate its prompt."
            )

        while content_budget > 0:
            segments = self.token_counter.split_text(
                summary,
                content_budget,
            )

            largest_overage = 0

            for segment in segments:
                reduce_tokens = self._estimate_prompt_tokens(
                    self.reduce_prompt,
                    summaries=segment,
                )

                final_tokens = self._estimate_prompt_tokens(
                    self.final_prompt,
                    summaries=segment,
                )

                largest_overage = max(
                    largest_overage,
                    reduce_tokens - self.REDUCE_INPUT_TOKEN_BUDGET,
                    final_tokens - self.FINAL_INPUT_TOKEN_BUDGET,
                )

            if largest_overage <= 0:
                return segments

            content_budget -= max(largest_overage, 8)

        raise ValueError(
            "Unable to split an intermediate summary "
            "within both REDUCE and FINAL token budgets."
        )

    def _prepare_summaries_for_reduction(
            self,
            summaries: Sequence[str],
    ) -> list[str]:

        prepared = []

        if any(not summary.strip() for summary in summaries):
            raise ValueError("Intermediate summaries must not be empty.")

        for summary in summaries:
            reduce_tokens = self._estimate_prompt_tokens(
                self.reduce_prompt,
                summaries=summary,
            )

            final_tokens = self._estimate_prompt_tokens(
                self.final_prompt,
                summaries=summary,
            )

            if (
                    reduce_tokens > self.REDUCE_INPUT_TOKEN_BUDGET
                    or final_tokens > self.FINAL_INPUT_TOKEN_BUDGET
            ):
                prepared.extend(
                    self._split_summary_to_fit_budgets(summary)
                )
            else:
                prepared.append(summary)

        return prepared

    @staticmethod
    def _extract_text(content: Any) -> str:

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            return "\n".join(
                block["text"]
                for block in content
                if isinstance(block, dict)
                and block.get("type") == "text"
            ).strip()

        raise TypeError(
            f"Unexpected LLM response content type: {type(content)}"
        )
