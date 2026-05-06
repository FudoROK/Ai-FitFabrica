from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContextValidationErrorCode(StrEnum):
    """Machine-readable failure reasons for source-context validation."""

    INVALID_INPUT = "invalid_input"
    UNKNOWN_CANDIDATE = "unknown_candidate"
    INVALID_TRANSITION = "invalid_transition"
    MISSING_AUTHORITY = "missing_authority"
    MISSING_REFINED_VALUE = "missing_refined_value"
    PERSISTENCE_FAILURE = "persistence_failure"
    STALE_STATE = "stale_state"


class SourceContextCandidateStatus(StrEnum):
    """Lifecycle states for non-authoritative source-derived context."""

    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    REFINED = "refined"
    REJECTED = "rejected"
    OPEN = "open"


class ValidationDecision(StrEnum):
    """Explicit backend-supported decisions for a candidate."""

    CONFIRM = "confirm"
    REFINE = "refine"
    REJECT = "reject"
    KEEP_OPEN = "keep_open"


class SourceContextPayload(BaseModel):
    """Normalized context content extracted from a source."""

    model_config = ConfigDict(extra="forbid")

    fact_key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class SourceReference(BaseModel):
    """Traceable source information for a candidate."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_excerpt: str | None = None


class ActorContext(BaseModel):
    """Identity context for backend-owned state transitions."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    session_id: str | None = None


class SourceContextCandidate(BaseModel):
    """Non-authoritative candidate state awaiting explicit validation."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    payload: SourceContextPayload
    source_reference: SourceReference
    actor_context: ActorContext
    status: SourceContextCandidateStatus
    correlation_id: str = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_fact_id: str | None = None
    validation_reason: str | None = None


class ConfirmedFact(BaseModel):
    """Authoritative fact promoted by an accepted validation decision."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    fact_key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    source_reference: SourceReference
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceContextCandidateCommand(BaseModel):
    """Command to register source-derived content as candidate state."""

    model_config = ConfigDict(extra="forbid")

    payload: SourceContextPayload
    source_reference: SourceReference
    actor_context: ActorContext
    correlation_id: str = Field(min_length=1)


class SourceContextValidationCommand(BaseModel):
    """Command to validate one pending source-context candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    decision: ValidationDecision
    actor_context: ActorContext
    correlation_id: str = Field(min_length=1)
    refined_value: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def require_refined_value_for_refine(self) -> SourceContextValidationCommand:
        """Reject refine decisions that do not provide a replacement value."""
        if self.decision == ValidationDecision.REFINE and not (self.refined_value or "").strip():
            raise ValueError("refined_value is required for refine decisions")
        return self


class ContextValidationError(BaseModel):
    """Structured backend error returned by validation use cases."""

    model_config = ConfigDict(extra="forbid")

    code: ContextValidationErrorCode
    message: str


class SourceContextValidationResult(BaseModel):
    """Backend result for candidate creation or validation."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    candidate: SourceContextCandidate | None = None
    confirmed_fact: ConfirmedFact | None = None
    error: ContextValidationError | None = None
    audit_summary: str


class ContextStateQuery(BaseModel):
    """Query for separated confirmed fact and candidate state."""

    model_config = ConfigDict(extra="forbid")

    actor_context: ActorContext
    include_candidates: bool = True
    include_confirmed_facts: bool = True


class ContextStateQueryResult(BaseModel):
    """Read model that keeps candidates separate from confirmed facts."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    confirmed_facts: list[ConfirmedFact] = Field(default_factory=list)
    candidates: list[SourceContextCandidate] = Field(default_factory=list)
    error: ContextValidationError | None = None
