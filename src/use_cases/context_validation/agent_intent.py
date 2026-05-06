from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from src.domain.context_validation import SourceContextPayload, SourceReference, ValidationDecision


class CandidateProposal(BaseModel):
    """Structured source-context candidate proposed by an agent."""

    model_config = ConfigDict(extra="forbid")

    payload: SourceContextPayload
    source_reference: SourceReference
    confidence: float = Field(ge=0.0, le=1.0)


class ValidationRecommendation(BaseModel):
    """Advisory validation recommendation emitted by an agent."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    decision: ValidationDecision
    refined_value: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def require_refined_value_for_refine(self) -> ValidationRecommendation:
        """Require a refined value when the agent recommends refinement."""
        if self.decision == ValidationDecision.REFINE and not (self.refined_value or "").strip():
            raise ValueError("refined_value is required for refine recommendations")
        return self


class SourceContextValidationIntent(BaseModel):
    """Structured JSON intent accepted from source-context validation agents."""

    model_config = ConfigDict(extra="forbid")

    candidate_proposals: list[CandidateProposal] = Field(default_factory=list)
    validation_recommendations: list[ValidationRecommendation] = Field(default_factory=list)
    uncertainty_reason: str | None = None

    @classmethod
    def parse_agent_payload(cls, payload: object) -> SourceContextValidationIntent:
        """Parse agent output and reject malformed or unsupported structures."""
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"invalid_source_context_validation_intent: {exc}") from exc
