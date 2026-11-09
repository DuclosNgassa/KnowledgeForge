import json
from pathlib import Path

from evaluation.extraction.schemas import ExtractionEvaluationSample

"""
Reads a JSON dataset.
Validates each sample with Pydantic.
Rejects duplicate sample IDs.
Fails early if the dataset is missing or incorrectly structured.
"""


def load_extraction_dataset(
        file_path: str | Path,
) -> list[ExtractionEvaluationSample]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Extraction evaluation dataset not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if not isinstance(raw_data, list):
        raise ValueError(
            "Extraction evaluation dataset must contain a JSON array."
        )

    samples = [
        ExtractionEvaluationSample.model_validate(item)
        for item in raw_data
    ]

    sample_ids = [sample.id for sample in samples]

    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError(
            "Extraction evaluation dataset contains duplicate sample IDs."
        )

    return samples
