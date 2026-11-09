import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.core.settings import settings
from app.core.db.database import AsyncSessionLocal  # Adjust to your project
from app.observability.logging import logger
from app.schemas.document_extraction import DocumentExtractionResult
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)

from evaluation.extraction.dataset_loader import (
    load_extraction_dataset,
)
from evaluation.extraction.evaluator import evaluate_extraction
from evaluation.extraction.reporting import (
    generate_evaluation_report,
    save_evaluation_report,
)
from evaluation.extraction.schemas import SkippedEvaluationSample
from evaluation.extraction.semantic_judge import (
    SemanticFindingEvaluator,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR.parent / "datasets" / "extraction_dataset.json"
REPORT_DIR = BASE_DIR / "reports"


async def load_predictions(dataset):
    """
    Load completed extraction results from PostgreSQL.

    Database access is completed before any LLM evaluation starts.
    """
    predictions = {}
    skipped_samples = []

    async with AsyncSessionLocal() as db:
        repository = DocumentExtractionRepository(db)

        for sample in dataset:
            extraction = await repository.find_by_document_id(
                sample.document_id
            )

            if extraction is None:
                skipped_samples.append(
                    SkippedEvaluationSample(
                        sample_id=sample.id,
                        document_id=sample.document_id,
                        reason="No extraction record found.",
                    )
                )
                continue

            status = getattr(
                extraction.status,
                "value",
                extraction.status,
            )

            if status != "COMPLETED":
                skipped_samples.append(
                    SkippedEvaluationSample(
                        sample_id=sample.id,
                        document_id=sample.document_id,
                        reason=f"Extraction status is {status}.",
                    )
                )
                continue

            if extraction.extraction_data is None:
                skipped_samples.append(
                    SkippedEvaluationSample(
                        sample_id=sample.id,
                        document_id=sample.document_id,
                        reason="Extraction data is empty.",
                    )
                )
                continue

            try:
                predictions[sample.id] = (
                    DocumentExtractionResult.model_validate(
                        extraction.extraction_data
                    )
                )
            except Exception as exc:
                logger.exception(
                    "Invalid extraction data for document %s",
                    sample.document_id,
                )

                skipped_samples.append(
                    SkippedEvaluationSample(
                        sample_id=sample.id,
                        document_id=sample.document_id,
                        reason=f"Invalid extraction data: {exc}",
                    )
                )

    return predictions, skipped_samples


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    logger.info("Loading extraction evaluation dataset...")

    dataset = load_extraction_dataset(DATASET_PATH)

    logger.info("Loaded %d evaluation samples.", len(dataset))

    logger.info("Loading predictions from PostgreSQL...")

    predictions, skipped_samples = await load_predictions(dataset)

    logger.info(
        "Loaded %d predictions; skipped %d samples.",
        len(predictions),
        len(skipped_samples),
    )

    if not predictions:
        logger.warning("No completed extractions available for evaluation.")
        return

    finding_evaluator = SemanticFindingEvaluator()

    results = []

    for sample in dataset:
        predicted = predictions.get(sample.id)

        if predicted is None:
            continue

        try:
            result = await evaluate_extraction(
                sample=sample,
                predicted=predicted,
                finding_evaluator=finding_evaluator,
            )

            results.append(result)

            logger.info(
                "%s | Overall F1: %.3f | Findings F1: %.3f",
                sample.id,
                result.overall_f1,
                result.findings.f1,
            )

        except Exception:
            logger.exception(
                "Evaluation failed for sample %s",
                sample.id,
            )

            skipped_samples.append(
                SkippedEvaluationSample(
                    sample_id=sample.id,
                    document_id=sample.document_id,
                    reason="Evaluation failed; see runner logs.",
                )
            )

    if not results:
        logger.warning("No samples were successfully evaluated.")
        return

    report = generate_evaluation_report(
        results=results,
        model_name=settings.openai_chat_model,
        dataset_name=DATASET_PATH.stem,
        skipped_samples=skipped_samples,
    )

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
            REPORT_DIR / f"extraction_evaluation_{timestamp}.json"
    )

    save_evaluation_report(
        report=report,
        output_path=output_path,
    )

    summary = report.summary

    logger.info("Evaluation completed.")
    logger.info("Evaluated: %d", summary.total_samples)
    logger.info("Skipped: %d", len(skipped_samples))
    logger.info("Overall precision: %.3f", summary.overall.precision)
    logger.info("Overall recall: %.3f", summary.overall.recall)
    logger.info("Overall F1: %.3f", summary.overall.f1)
    logger.info("Report saved to: %s", output_path)


if __name__ == "__main__":
    asyncio.run(main())
