import asyncio
from collections.abc import Sequence
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from app.models.document_chunk import DocumentChunk


class DocumentSummarizationAgent:
    MAP_BATCH_CHARS = 20_000
    REDUCE_BATCH_CHARS = 20_000
    FINAL_INPUT_CHARS = 20_000
    MAX_CONCURRENCY = 5

    def __init__(self, model: BaseChatModel):
        self.model = model
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENCY)

        self.map_chain = (
                ChatPromptTemplate.from_messages([
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
                | self.model
        )

        self.reduce_chain = (
                ChatPromptTemplate.from_messages([
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
                | self.model
        )

        self.final_chain = (
                ChatPromptTemplate.from_messages([
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
                | self.model
        )

    async def summarize(
            self,
            chunks: Sequence[DocumentChunk],
    ) -> str:

        if not chunks:
            raise ValueError("Cannot summarize an empty document")

        ordered_chunks = sorted(
            chunks,
            key=lambda chunk: chunk.chunk_index,
        )

        # Step 1: Group original chunks into batches
        chunk_batches = self._group_chunks(ordered_chunks)

        # Step 2: MAP - summarize chunk batches concurrently
        map_results = await asyncio.gather(
            *[
                self._invoke_map(batch)
                for batch in chunk_batches
            ]
        )

        # Step 3: REDUCE - recursively reduce intermediate summaries
        reduced_summaries = await self._recursive_reduce(map_results)

        # Step 4: Generate final document summary
        result = await self.final_chain.ainvoke({
            "summaries": "\n\n".join(reduced_summaries),
        })

        return self._extract_text(result.content)

    def _group_chunks(
            self,
            chunks: Sequence[DocumentChunk],
    ) -> list[list[DocumentChunk]]:

        batches: list[list[DocumentChunk]] = []
        current_batch: list[DocumentChunk] = []
        current_size = 0

        for chunk in chunks:
            chunk_size = len(chunk.content)

            if (
                    current_batch
                    and current_size + chunk_size > self.MAP_BATCH_CHARS
            ):
                batches.append(current_batch)
                current_batch = []
                current_size = 0

            current_batch.append(chunk)
            current_size += chunk_size

        if current_batch:
            batches.append(current_batch)

        return batches

    async def _invoke_map(
            self,
            chunks: Sequence[DocumentChunk],
    ) -> str:

        sections = []

        for chunk in chunks:
            page_info = (
                f", page {chunk.page_number}"
                if chunk.page_number is not None
                else ""
            )

            sections.append(
                f"[Chunk {chunk.chunk_index}{page_info}]\n"
                f"{chunk.content}"
            )

        async with self.semaphore:
            result = await self.map_chain.ainvoke({
                "text": "\n\n".join(sections),
            })

        return self._extract_text(result.content)

    async def _recursive_reduce(
            self,
            summaries: list[str],
    ) -> list[str]:

        current = summaries

        while self._total_chars(current) > self.FINAL_INPUT_CHARS:

            batches = self._group_texts(
                current,
                self.REDUCE_BATCH_CHARS,
            )

            # Every batch must contain at least two summaries.
            # Otherwise, this reduction round cannot make progress.
            if any(len(batch) < 2 for batch in batches):
                raise ValueError(
                    "Unable to reduce summaries within the configured "
                    "input size. Consider increasing REDUCE_BATCH_CHARS."
                )

            reduced = await asyncio.gather(
                *[
                    self._invoke_reduce(batch)
                    for batch in batches
                ]
            )

            if len(reduced) >= len(current):
                raise RuntimeError(
                    "Recursive summarization did not reduce "
                    "the number of summaries"
                )

            current = reduced

        return current

    async def _invoke_reduce(
            self,
            summaries: Sequence[str],
    ) -> str:

        async with self.semaphore:
            result = await self.reduce_chain.ainvoke({
                "summaries": "\n\n".join(summaries),
            })

        return self._extract_text(result.content)

    @staticmethod
    def _group_texts(
            texts: Sequence[str],
            max_chars: int,
    ) -> list[list[str]]:

        batches: list[list[str]] = []
        current_batch: list[str] = []
        current_size = 0

        for text in texts:
            text_size = len(text)

            if (
                    current_batch
                    and current_size + text_size > max_chars
            ):
                batches.append(current_batch)
                current_batch = []
                current_size = 0

            current_batch.append(text)
            current_size += text_size

        if current_batch:
            batches.append(current_batch)

        return batches

    @staticmethod
    def _total_chars(texts: Sequence[str]) -> int:
        return sum(len(text) for text in texts)

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
