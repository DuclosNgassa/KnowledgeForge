import pytest

from evaluation.extraction.aggregator import (
    aggregate_evaluation_results,
)
from evaluation.extraction.schemas import (
    ExtractionEvaluationResult,
    MetricScores,
)


def create_result(
        sample_id: str,
        category_correct: bool,
        topics_f1: float,
        entities_f1: float,
        entity_type_accuracy: float,
        technologies_f1: float,
        dates_f1: float,
        date_description_accuracy: float,
        findings_f1: float,
        overall_f1: float,
) -> ExtractionEvaluationResult:
    return ExtractionEvaluationResult(
        sample_id=sample_id,
        document_id=f"document-{sample_id}",
        document_category_correct=category_correct,

        topics=MetricScores(
            precision=topics_f1,
            recall=topics_f1,
            f1=topics_f1,
        ),

        entities=MetricScores(
            precision=entities_f1,
            recall=entities_f1,
            f1=entities_f1,
        ),

        entity_type_accuracy=entity_type_accuracy,

        technologies=MetricScores(
            precision=technologies_f1,
            recall=technologies_f1,
            f1=technologies_f1,
        ),

        dates=MetricScores(
            precision=dates_f1,
            recall=dates_f1,
            f1=dates_f1,
        ),

        date_description_accuracy=date_description_accuracy,

        findings=MetricScores(
            precision=findings_f1,
            recall=findings_f1,
            f1=findings_f1,
        ),

        overall_precision=overall_f1,
        overall_recall=overall_f1,
        overall_f1=overall_f1,
    )


def test_aggregate_evaluation_results():
    result_1 = create_result(
        sample_id="sample-001",
        category_correct=True,
        topics_f1=1.0,
        entities_f1=0.8,
        entity_type_accuracy=1.0,
        technologies_f1=0.9,
        dates_f1=1.0,
        date_description_accuracy=0.8,
        findings_f1=0.8,
        overall_f1=0.9,
    )

    result_2 = create_result(
        sample_id="sample-002",
        category_correct=False,
        topics_f1=0.6,
        entities_f1=0.6,
        entity_type_accuracy=0.5,
        technologies_f1=0.7,
        dates_f1=0.4,
        date_description_accuracy=0.6,
        findings_f1=0.6,
        overall_f1=0.7,
    )

    summary = aggregate_evaluation_results(
        [result_1, result_2]
    )

    assert summary.total_samples == 2

    # Category accuracy: (1 + 0) / 2
    assert summary.category_accuracy == pytest.approx(0.5)

    # Topics F1: (1.0 + 0.6) / 2
    assert summary.topics.f1 == pytest.approx(0.8)

    # Entities F1: (0.8 + 0.6) / 2
    assert summary.entities.f1 == pytest.approx(0.7)

    # Entity type accuracy: (1.0 + 0.5) / 2
    assert summary.entity_type_accuracy == pytest.approx(0.75)

    # Technologies F1: (0.9 + 0.7) / 2
    assert summary.technologies.f1 == pytest.approx(0.8)

    # Dates F1: (1.0 + 0.4) / 2
    assert summary.dates.f1 == pytest.approx(0.7)

    # Date description accuracy: (0.8 + 0.6) / 2
    assert summary.date_description_accuracy == pytest.approx(0.7)

    # Findings F1: (0.8 + 0.6) / 2
    assert summary.findings.f1 == pytest.approx(0.7)

    # Overall F1: (0.9 + 0.7) / 2
    assert summary.overall.f1 == pytest.approx(0.8)


def test_aggregation_rejects_empty_results():
    with pytest.raises(ValueError):
        aggregate_evaluation_results([])
