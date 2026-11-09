from statistics import mean

from evaluation.extraction.schemas import (
    ExtractionEvaluationResult,
    ExtractionEvaluationSummary,
    MetricSummary,
)


def aggregate_metric_scores(results, attribute: str) -> MetricSummary:
    scores = [getattr(result, attribute) for result in results]

    return MetricSummary(
        precision=mean(score.precision for score in scores),
        recall=mean(score.recall for score in scores),
        f1=mean(score.f1 for score in scores),
    )


def aggregate_evaluation_results(
        results: list[ExtractionEvaluationResult],
) -> ExtractionEvaluationSummary:
    if not results:
        raise ValueError("Cannot aggregate an empty evaluation result list.")

    return ExtractionEvaluationSummary(
        total_samples=len(results),

        category_accuracy=mean(
            result.document_category_correct
            for result in results
        ),

        topics=aggregate_metric_scores(results, "topics"),
        entities=aggregate_metric_scores(results, "entities"),

        entity_type_accuracy=mean(
            result.entity_type_accuracy
            for result in results
        ),

        technologies=aggregate_metric_scores(
            results,
            "technologies",
        ),

        dates=aggregate_metric_scores(results, "dates"),

        date_description_accuracy=mean(
            result.date_description_accuracy
            for result in results
        ),

        findings=aggregate_metric_scores(results, "findings"),

        overall=MetricSummary(
            precision=mean(result.overall_precision for result in results),
            recall=mean(result.overall_recall for result in results),
            f1=mean(result.overall_f1 for result in results),
        ),
    )
