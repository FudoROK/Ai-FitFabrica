"""Domain contracts for the Try-On sandbox lifecycle."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class TryOnWorkflowType(StrEnum):
    """Backend-owned workflow identifiers for Try-On jobs."""

    TRY_ON = "try_on"


class TryOnJobStatus(StrEnum):
    """Allowed lifecycle states for a Try-On sandbox job."""

    ACCEPTED = "accepted"
    VALIDATING_INPUTS = "validating_inputs"
    GENERATING = "generating"
    QUALITY_CHECKING = "quality_checking"
    COMPLETED = "completed"
    FAILED = "failed"


class TryOnSandboxLifecycleMode(StrEnum):
    """Sandbox-only lifecycle modes for exercising async client behavior."""

    COMPLETE = "complete"
    PENDING = "pending"
    FAILED = "failed"


class TryOnUploadRole(StrEnum):
    """Required upload roles accepted by the Try-On sandbox."""

    HUMAN_PHOTO = "human_photo"
    GARMENT_PHOTO = "garment_photo"


class TryOnChargeStatus(StrEnum):
    """Charge states supported by the initial sandbox contract."""

    NOT_CHARGED = "not_charged"


class TryOnErrorCode(StrEnum):
    """Typed error codes returned by Try-On sandbox endpoints."""

    MISSING_REQUIRED_FILE = "missing_required_file"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    EMPTY_FILE = "empty_file"
    FILE_TOO_LARGE = "file_too_large"
    JOB_NOT_FOUND = "job_not_found"
    RESULT_NOT_READY = "result_not_ready"
    JOB_FAILED = "job_failed"
    STORAGE_UNAVAILABLE = "storage_unavailable"


class TryOnInputMetadata(BaseModel):
    """Sanitized metadata for a user-uploaded Try-On input file."""

    model_config = ConfigDict(extra="forbid")

    role: TryOnUploadRole
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("sha256")
    @classmethod
    def _validate_sha256_hex(cls, value: str) -> str:
        """Require a full SHA-256 digest encoded as 64 hexadecimal characters."""
        if not all(char in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("sha256 must be 64 hexadecimal characters")
        return value


class TryOnStoredInput(BaseModel):
    """Backend-owned storage reference for a persisted Try-On input file."""

    model_config = ConfigDict(extra="forbid")

    role: TryOnUploadRole
    storage_backend: Literal["in_memory", "gcs"]
    uri: str = Field(min_length=1)
    bucket_name: str | None = None
    object_name: str | None = None
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("sha256")
    @classmethod
    def _validate_sha256_hex(cls, value: str) -> str:
        """Require a full SHA-256 digest encoded as 64 hexadecimal characters."""
        if not all(char in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("sha256 must be 64 hexadecimal characters")
        return value


class TryOnStatusEvent(BaseModel):
    """Append-only status transition event for a Try-On job."""

    model_config = ConfigDict(extra="forbid")

    status: TryOnJobStatus
    stage: str = Field(min_length=1)
    message: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=utc_now)


class TryOnCostEvent(BaseModel):
    """Sandbox cost event emitted by backend workflow ownership."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    estimated_units: int = Field(ge=0)
    charge_status: TryOnChargeStatus = TryOnChargeStatus.NOT_CHARGED
    charged_credits: int = Field(ge=0)
    occurred_at: datetime = Field(default_factory=utc_now)


class TryOnQualityCheck(BaseModel):
    """Single deterministic quality check result for a Try-On output."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    status: Literal["passed", "warning", "failed"]
    confidence: float = Field(ge=0.0, le=1.0)
    message: str = Field(min_length=1)


class TryOnQualityReport(BaseModel):
    """Quality verifier report attached before a result is exposed."""

    model_config = ConfigDict(extra="forbid")

    verdict: Literal["pass", "repair_recommended", "reject"]
    confidence: float = Field(ge=0.0, le=1.0)
    checks: list[TryOnQualityCheck] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class TryOnResultImage(BaseModel):
    """Public metadata for a generated Try-On result image."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["sandbox_placeholder"]
    url: str = Field(min_length=1)
    alt: str = Field(min_length=1)


class TryOnResult(BaseModel):
    """Completed Try-On result returned after quality verification."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    result_image: TryOnResultImage
    quality_report: TryOnQualityReport
    stylist_note: str = Field(min_length=1)
    input_metadata: list[TryOnInputMetadata] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=utc_now)


class TryOnError(BaseModel):
    """Structured Try-On error safe for API responses."""

    model_config = ConfigDict(extra="forbid")

    code: TryOnErrorCode
    message: str = Field(min_length=1)
    details: dict[str, object] = Field(default_factory=dict)


class TryOnJob(BaseModel):
    """Backend-owned aggregate for one Try-On sandbox job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    status: TryOnJobStatus
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    input_metadata: list[TryOnInputMetadata] = Field(default_factory=list)
    stored_inputs: list[TryOnStoredInput] = Field(default_factory=list)
    status_history: list[TryOnStatusEvent] = Field(default_factory=list)
    cost_events: list[TryOnCostEvent] = Field(default_factory=list)
    result: TryOnResult | None = None
    error: TryOnError | None = None


class TryOnJobCreatedResponse(BaseModel):
    """API response returned when a Try-On job is accepted."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    status: TryOnJobStatus
    input_metadata: list[TryOnInputMetadata] = Field(default_factory=list)
    status_url: str = Field(min_length=1)
    result_url: str = Field(min_length=1)


class TryOnJobStatusResponse(BaseModel):
    """API response returned for Try-On status polling."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    status: TryOnJobStatus
    status_history: list[TryOnStatusEvent] = Field(default_factory=list)
    cost_events: list[TryOnCostEvent] = Field(default_factory=list)


class TryOnResultResponse(BaseModel):
    """API response returned when a Try-On result is ready."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["completed"]
    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    result: TryOnResult


class TryOnNotReadyResponse(BaseModel):
    """API response returned when a Try-On result is not available yet."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["not_ready"]
    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    current_status: TryOnJobStatus
    status_url: str = Field(min_length=1)


class TryOnErrorResponse(BaseModel):
    """API response wrapper for typed Try-On errors."""

    model_config = ConfigDict(extra="forbid")

    error: TryOnError
