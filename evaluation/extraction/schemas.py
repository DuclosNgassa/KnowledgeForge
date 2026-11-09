from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.schemas.document_extraction import DocumentExtractionResult


class ExtractionEvaluationSample(BaseModel):
    id: str
    document_id: str
    expected_extraction: DocumentExtractionResult
    description: str | None = None


class MetricScores(BaseModel):
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)


class ExtractionEvaluationResult(BaseModel):
    sample_id: str
    document_id: str
    document_category_correct: bool
    topics: MetricScores
    entities: MetricScores
    entity_type_accuracy: float = Field(ge=0.0, le=1.0)
    technologies: MetricScores
    dates: MetricScores
    date_description_accuracy: float = Field(ge=0.0, le=1.0)
    findings: MetricScores
    overall_precision: float
    overall_recall: float
    overall_f1: float


class FindingMatch(BaseModel):
    expected_index: int = Field(
        ge=0,
        description="Index of the expected finding.",
    )
    predicted_index: int = Field(
        ge=0,
        description="Index of the predicted finding.",
    )
    is_equivalent: bool = Field(
        description="Whether both findings express the same meaning.",
    )
    explanation: str = Field(
        description="Brief explanation of the semantic comparison.",
    )


class FindingJudgeResponse(BaseModel):
    matches: list[FindingMatch] = Field(
        default_factory=list,
        description="One-to-one comparisons between equivalent findings.",
    )


class MetricSummary(BaseModel):
    precision: float
    recall: float
    f1: float


class ExtractionEvaluationSummary(BaseModel):
    total_samples: int

    category_accuracy: float

    topics: MetricSummary
    entities: MetricSummary
    entity_type_accuracy: float
    technologies: MetricSummary
    dates: MetricSummary
    date_description_accuracy: float
    findings: MetricSummary

    overall: MetricSummary


class SkippedEvaluationSample(BaseModel):
    sample_id: str
    document_id: str
    reason: str


class ExtractionEvaluationReport(BaseModel):
    evaluation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    model_name: str
    dataset_name: str
    summary: ExtractionEvaluationSummary
    results: list[ExtractionEvaluationResult]

    skipped_samples: list[SkippedEvaluationSample] = Field(
        default_factory=list
    )
