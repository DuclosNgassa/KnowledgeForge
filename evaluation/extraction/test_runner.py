from datetime import date

from app.schemas.document_extraction import ExtractedEntity, ExtractedDate
from evaluation.extraction.dataset_loader import load_extraction_dataset
from evaluation.extraction.metrics import calculate_entity_scores, calculate_date_scores
from evaluation.extraction.semantic_judge import SemanticFindingEvaluator

evaluator = SemanticFindingEvaluator()

samples = load_extraction_dataset(
    "evaluation/evaluation_datasets/extraction_dataset.json"
)

sample = samples[0]

# Example: use the reference extraction as prediction.
predicted = sample.expected_extraction

# result = await evaluate_extraction(
#     sample=sample,
#     predicted=predicted,
#     finding_evaluator=evaluator,
# )

# print(result.model_dump_json(indent=2))

expected = [
    ExtractedEntity(
        name="Spring Boot",
        entity_type="TECHNOLOGY",
        description="Java framework",
    ),
    ExtractedEntity(
        name="Apache Kafka",
        entity_type="TECHNOLOGY",
        description="Event streaming platform",
    ),
]

predicted = [
    ExtractedEntity(
        name="spring boot",
        entity_type="FRAMEWORK",
        description="Framework for Java applications",
    ),
    ExtractedEntity(
        name="Apache Kafka",
        entity_type="TECHNOLOGY",
        description="Distributed messaging system",
    ),
    ExtractedEntity(
        name="PostgreSQL",
        entity_type="DATABASE",
        description="Relational database",
    ),
]

scores, type_accuracy = calculate_entity_scores(expected, predicted)
print("\n")
print(scores)
print("Entity type accuracy:", type_accuracy)

expected = [
    ExtractedDate(
        date=date(2026, 3, 15),
        description="Project launch date",
    ),
    ExtractedDate(
        date=date(2026, 6, 20),
        description="Contract expiration date",
    ),
]

predicted = [
    ExtractedDate(
        date=date(2026, 3, 15),
        description="The project was officially launched",
    ),
    ExtractedDate(
        date=date(2026, 7, 1),
        description="Contract expiration date",
    ),
]

scores, description_accuracy = calculate_date_scores(
    expected=expected,
    predicted=predicted,
)

print("\n")
print("Date scores:", scores)
print("Date description accuracy:", description_accuracy)


async def test_semantic_findings():
    expected = [
        "The application uses PostgreSQL for persistent data storage.",
        "The system supports asynchronous document processing.",
    ]

    predicted = [
        "PostgreSQL is the primary database of the application.",
        "Document processing is handled asynchronously.",
        "The application uses MongoDB for caching.",
    ]

    scores = await evaluator.evaluate(
        expected=expected,
        predicted=predicted,
    )

    print("\n")
    print("Precision:", scores.precision)
    print("Recall:", scores.recall)
    print("F1:", scores.f1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_semantic_findings())
