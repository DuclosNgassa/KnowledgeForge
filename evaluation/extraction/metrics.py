import re
import unicodedata
from collections.abc import Iterable

from app.schemas.document_extraction import (
    ExtractedEntity,
    ExtractedDate,
)
from evaluation.extraction.schemas import (
    MetricScores,
)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def calculate_entity_scores(
        expected: list[ExtractedEntity],
        predicted: list[ExtractedEntity],
) -> tuple[MetricScores, float]:
    # Entity detection: compare names, independently of entity type.
    expected_names = [
        normalize_text(entity.name)
        for entity in expected
    ]

    predicted_names = [
        normalize_text(entity.name)
        for entity in predicted
    ]

    detection_scores = calculate_scores(
        expected_names,
        predicted_names,
    )

    # Entity type accuracy: compare types for entities
    # whose names were correctly detected.
    expected_by_name = {
        normalize_text(entity.name): normalize_text(entity.entity_type)
        for entity in expected
    }

    predicted_by_name = {
        normalize_text(entity.name): normalize_text(entity.entity_type)
        for entity in predicted
    }

    matched_names = expected_by_name.keys() & predicted_by_name.keys()

    if not expected and not predicted:
        type_accuracy = 1.0
    elif not matched_names:
        type_accuracy = 0.0
    else:
        correct_types = sum(
            expected_by_name[name] == predicted_by_name[name]
            for name in matched_names
        )

        type_accuracy = correct_types / len(matched_names)

    return detection_scores, type_accuracy


def calculate_scores(
        expected: Iterable[str],
        predicted: Iterable[str],
) -> MetricScores:
    expected_set = {
        normalize_text(value)
        for value in expected
    }

    predicted_set = {
        normalize_text(value)
        for value in predicted
    }

    true_positives = len(expected_set & predicted_set)
    false_positives = len(predicted_set - expected_set)
    false_negatives = len(expected_set - predicted_set)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives > 0
        else 1.0
    )

    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives > 0
        else 1.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return MetricScores(
        precision=precision,
        recall=recall,
        f1=f1,
    )


def entity_key(entity: ExtractedEntity) -> str:
    return (
        f"{normalize_text(entity.name)}|"
        f"{normalize_text(entity.entity_type)}"
    )


def date_key(item: ExtractedDate) -> str:
    return item.date.isoformat()


def calculate_overall_scores(
        metrics: list[MetricScores],
) -> MetricScores:
    if not metrics:
        return MetricScores(
            precision=1.0,
            recall=1.0,
            f1=1.0,
        )

    count = len(metrics)

    return MetricScores(
        precision=sum(m.precision for m in metrics) / count,
        recall=sum(m.recall for m in metrics) / count,
        f1=sum(m.f1 for m in metrics) / count,
    )


def calculate_date_scores(
        expected: list[ExtractedDate],
        predicted: list[ExtractedDate],
) -> tuple[MetricScores, float]:
    # Match dates independently of their descriptions.
    expected_by_date = {
        item.date.isoformat(): normalize_text(item.description)
        for item in expected
    }

    predicted_by_date = {
        item.date.isoformat(): normalize_text(item.description)
        for item in predicted
    }

    date_scores = calculate_scores(
        list(expected_by_date.keys()),
        list(predicted_by_date.keys()),
    )

    # Evaluate descriptions only for correctly detected dates.
    matched_dates = expected_by_date.keys() & predicted_by_date.keys()

    if not expected and not predicted:
        description_accuracy = 1.0
    elif not matched_dates:
        description_accuracy = 0.0
    else:
        correct_descriptions = sum(
            expected_by_date[date] == predicted_by_date[date]
            for date in matched_dates
        )

        description_accuracy = (
                correct_descriptions / len(matched_dates)
        )

    return date_scores, description_accuracy
