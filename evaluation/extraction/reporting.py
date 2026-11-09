import json
from pathlib import Path

from evaluation.extraction.schemas import (
    ExtractionEvaluationReport,
    ExtractionEvaluationResult, SkippedEvaluationSample,
)
from evaluation.extraction.aggregator import (
    aggregate_evaluation_results,
)


def generate_evaluation_report(
        results: list[ExtractionEvaluationResult],
        model_name: str,
        dataset_name: str,
        skipped_samples: list[SkippedEvaluationSample] | None = None,
) -> ExtractionEvaluationReport:
    summary = aggregate_evaluation_results(results)

    return ExtractionEvaluationReport(
        model_name=model_name,
        dataset_name=dataset_name,
        summary=summary,
        results=results,
        skipped_samples=skipped_samples or [],
    )


def save_evaluation_report(
        report: ExtractionEvaluationReport,
        output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            report.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
