from app.schemas.document_extraction import DocumentExtractionResult
from evaluation.extraction.metrics import calculate_scores, calculate_entity_scores, calculate_date_scores, \
    normalize_text, calculate_overall_scores
from evaluation.extraction.schemas import ExtractionEvaluationSample, ExtractionEvaluationResult
from evaluation.extraction.semantic_judge import SemanticFindingEvaluator


async def evaluate_extraction(
        sample: ExtractionEvaluationSample,
        predicted: DocumentExtractionResult,
        finding_evaluator: SemanticFindingEvaluator,
) -> ExtractionEvaluationResult:
    expected = sample.expected_extraction

    topics = calculate_scores(
        expected=expected.key_topics,
        predicted=predicted.key_topics,
    )

    entities, entity_type_accuracy = calculate_entity_scores(
        expected=expected.named_entities,
        predicted=predicted.named_entities,
    )

    technologies = calculate_scores(
        expected=expected.technologies,
        predicted=predicted.technologies,
    )

    dates, date_description_accuracy = calculate_date_scores(
        expected=expected.important_dates,
        predicted=predicted.important_dates,
    )

    findings = await finding_evaluator.evaluate(
        expected=sample.expected_extraction.key_findings,
        predicted=predicted.key_findings,
    )

    category_correct = (
            normalize_text(expected.document_category)
            == normalize_text(predicted.document_category)
    )

    overall = calculate_overall_scores(
        [
            topics,
            entities,
            technologies,
            dates,
            findings,
        ]
    )

    return ExtractionEvaluationResult(
        sample_id=sample.id,
        document_id=sample.document_id,
        document_category_correct=category_correct,
        topics=topics,
        entities=entities,
        entity_type_accuracy=entity_type_accuracy,
        technologies=technologies,
        dates=dates,
        date_description_accuracy=date_description_accuracy,
        findings=findings,
        overall_precision=overall.precision,
        overall_recall=overall.recall,
        overall_f1=overall.f1,
    )
