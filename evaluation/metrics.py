"""
the first metrics should measure whether hybrid search, RRF
retrieve the chunks that the dataset identifies as relevant.
"""
from evaluation.schemas import EvaluationSample


def recall_at_k(
        expected_chunk_ids: set[str],
        retrieved_chunk_ids: list[str],
        k: int,
) -> float:
    """
    Recall@K: how many of the expected relevant chunks were retrieved.
    :param expected_chunk_ids:
    :param retrieved_chunk_ids:
    :param k:
    :return:
    """
    if not expected_chunk_ids:
        return 0.0

    retrieved = set(retrieved_chunk_ids[:k])

    return len(expected_chunk_ids & retrieved) / len(
        expected_chunk_ids
    )


def precision_at_k(
        expected_chunk_ids: set[str],
        retrieved_chunk_ids: list[str],
        k: int,
) -> float:
    """
    Precision@K: how many retrieved chunks are relevant.
    :param expected_chunk_ids:
    :param retrieved_chunk_ids:
    :param k:
    :return:
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    retrieved = retrieved_chunk_ids[:k]

    if not retrieved:
        return 0.0

    relevant_count = sum(
        chunk_id in expected_chunk_ids
        for chunk_id in retrieved
    )

    return relevant_count / k


def reciprocal_rank(
        expected_chunk_ids: set[str],
        retrieved_chunk_ids: list[str],
) -> float:
    """
    MRR: how highly the first relevant chunk ranks.
    :param expected_chunk_ids:
    :param retrieved_chunk_ids:
    :return:
    """
    for rank, chunk_id in enumerate(retrieved_chunk_ids, start=1):
        if chunk_id in expected_chunk_ids:
            return 1.0 / rank

    return 0.0


def hit_at_k(expected_chunk_ids: set[str],
             retrieved_chunk_ids: list[str]) -> float:
    return float(
        bool(expected_chunk_ids & set(retrieved_chunk_ids))
    )


def expected_chunk_ids(
        sample: EvaluationSample,
) -> set[str]:
    return {
        chunk["chunk_id"]
        for chunk in sample["relevant_chunks"]
    }
