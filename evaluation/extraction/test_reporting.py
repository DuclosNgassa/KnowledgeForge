import json

from evaluation.extraction.reporting import (
    generate_evaluation_report,
    save_evaluation_report,
)
from evaluation.extraction.schemas import (
    ExtractionEvaluationResult,
    MetricScores,
)


def create_sample_result() -> ExtractionEvaluationResult:
    return ExtractionEvaluationResult(
        sample_id="sample-001",
        document_id="document-001",
        document_category_correct=True,
        topics=MetricScores(
            precision=0.8,
            recall=0.9,
            f1=0.85,
        ),
        entities=MetricScores(
            precision=0.9,
            recall=0.8,
            f1=0.85,
        ),
        entity_type_accuracy=0.9,
        technologies=MetricScores(
            precision=1.0,
            recall=0.8,
            f1=0.89,
        ),
        dates=MetricScores(
            precision=0.8,
            recall=0.8,
            f1=0.8,
        ),
        date_description_accuracy=0.75,
        findings=MetricScores(
            precision=0.9,
            recall=0.9,
            f1=0.9,
        ),
        overall_precision=0.88,
        overall_recall=0.84,
        overall_f1=0.86,
    )


def test_generate_evaluation_report():
    result = create_sample_result()

    report = generate_evaluation_report(
        results=[result],
        model_name="openai:gpt-5-mini",
        dataset_name="extraction_dataset",
    )

    assert report.model_name == "openai:gpt-5-mini"
    assert report.dataset_name == "extraction_dataset"

    assert report.summary.total_samples == 1
    assert report.summary.category_accuracy == 1.0
    assert report.summary.findings.f1 == 0.9

    assert len(report.results) == 1
    assert report.results[0].sample_id == "sample-001"


def test_save_evaluation_report(tmp_path):
    result = create_sample_result()

    report = generate_evaluation_report(
        results=[result],
        model_name="openai:gpt-5-mini",
        dataset_name="extraction_dataset",
    )

    output_path = tmp_path / "reports" / "evaluation.json"

    save_evaluation_report(
        report=report,
        output_path=output_path,
    )

    assert output_path.exists()

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["model_name"] == "openai:gpt-5-mini"
    assert data["summary"]["total_samples"] == 1
    assert data["results"][0]["sample_id"] == "sample-001"
    assert "evaluation_timestamp" in data
