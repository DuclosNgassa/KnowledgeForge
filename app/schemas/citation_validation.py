from typing import Literal

from pydantic import BaseModel, Field


class ClaimAssessment(BaseModel):
    claim: str = Field(
        description="One factual claim stated in the answer."
    )
    citation_ids: list[str] = Field(
        default_factory=list,
        description="Citation IDs attached to this claim, such as D1 or W2.",
    )
    supported: bool = Field(
        description=(
            "True only when the supplied evidence directly supports "
            "the claim. Otherwise false."
        )
    )
    explanation: str = Field(
        description="Brief explanation based on the supplied evidence."
    )


class CitationGroundingResult(BaseModel):
    claims: list[ClaimAssessment] = Field(default_factory=list)


class CitationGroundingReport(BaseModel):
    claims: list[ClaimAssessment]
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    uncited_claims: int
    grounded_claim_ratio: float | None
    citation_coverage: float | None
    citation_support_rate: float | None
    invalid_citations: list[str]
