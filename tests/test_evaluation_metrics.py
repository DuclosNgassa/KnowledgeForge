from evaluation.retrieval_evaluator import calculate_metrics


def test_relevant_chunk_ranked_first():
    metrics = calculate_metrics(
        relevant_ids={"chunk-a", "chunk-b"},
        ranked_ids=["chunk-a", "chunk-c", "chunk-b"],
        k=5,
    )

    assert metrics.recall_at_5 == 1.0
    assert metrics.mrr_at_20 == 1.0
    assert metrics.hit_at_5 == 1.0


def test_relevant_chunk_missing():
    metrics = calculate_metrics(
        relevant_ids={"chunk-a"},
        ranked_ids=["chunk-b", "chunk-c"],
        k=5,
    )

    assert metrics.recall_at_5 == 0.0
    assert metrics.mrr_at_20 == 0.0
    assert metrics.hit_at_5 == 0.0
