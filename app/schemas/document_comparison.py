from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from dataclasses import dataclass

from app.models.enums import ComparisonStatus


@dataclass
class PrerequisiteDispatch:
    document_id: UUID
    summary_generation_id: UUID | None = None
    extraction_generation_id: UUID | None = None


class ComparisonCriterion(str, Enum):
    KEY_TOPICS = "key_topics"
    TECHNOLOGIES = "technologies"
    NAMED_ENTITIES = "named_entities"


class CreateDocumentComparisonRequest(BaseModel):
    document_ids: list[UUID] = Field(min_length=2)
    title: str | None = Field(default=None, max_length=255)
    criteria: list[ComparisonCriterion] = Field(
        min_length=1,
        default_factory=lambda: [
            ComparisonCriterion.KEY_TOPICS,
            ComparisonCriterion.TECHNOLOGIES,
            ComparisonCriterion.NAMED_ENTITIES,
        ],
    )

    @field_validator("document_ids")
    @classmethod
    def validate_unique_document_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Document IDs must be unique.")
        return value

    @field_validator("criteria")
    @classmethod
    def validate_unique_criteria(
            cls,
            value: list[ComparisonCriterion],
    ) -> list[ComparisonCriterion]:
        if len(value) != len(set(value)):
            raise ValueError("Comparison criteria must be unique.")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None


class DocumentInsight(BaseModel):
    document_id: UUID
    document_title: str | None
    insights: list[str] = Field(min_length=1)

    @field_validator("insights")
    @classmethod
    def validate_insights(cls, value: list[str]) -> list[str]:
        if any(not insight.strip() for insight in value):
            raise ValueError("Insights cannot contain empty strings.")
        return value


class CriterionComparisonResult(BaseModel):
    criterion: ComparisonCriterion
    similarities: list[str] = Field(min_length=1)
    differences: list[str] = Field(min_length=1)
    document_insights: list[DocumentInsight] = Field(min_length=2)


class DocumentComparisonResponse(BaseModel):
    overview: str
    criterion_results: list[CriterionComparisonResult] = Field(min_length=1)
    conclusion: str

    @field_validator("overview", "conclusion")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be empty.")
        return value.strip()


class CreateDocumentComparisonResponse(BaseModel):
    id: UUID
    title: str | None
    status: ComparisonStatus
    document_ids: list[UUID]
    criteria: list[ComparisonCriterion]
    created_at: datetime


class DocumentComparisonDetailResponse(BaseModel):
    id: UUID
    title: str | None
    status: ComparisonStatus
    document_ids: list[UUID]
    criteria: list[ComparisonCriterion]

    overview: str | None
    criterion_results: list[CriterionComparisonResult] | None
    conclusion: str | None

    error_message: str | None

    created_at: datetime
    updated_at: datetime
