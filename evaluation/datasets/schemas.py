from typing import TypedDict, Literal


class RelevantChunk(TypedDict):
    document_id: str
    chunk_id: str
    page_number: int | None


class EvaluationSample(TypedDict):
    id: str
    question: str
    expected_answer: str
    relevant_chunks: list[RelevantChunk]
    question_type: Literal[
        "factual",
        "semantic",
        "multi_chunk",
        "cross_document",
        "unanswerable",
    ]
    difficulty: Literal["easy", "medium", "hard"]
    answerable: bool
