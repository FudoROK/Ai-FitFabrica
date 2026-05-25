"""Domain contracts for the Try-On sandbox lifecycle."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | list[JsonPrimitive] | dict[str, JsonPrimitive | list[JsonPrimitive]]


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


class TryOnInputMetadata(BaseModel):
    """Sanitized metadata for a user-uploaded Try-On input file."""

    model_config = ConfigDict(extra="forbid")

    role: TryOnUploadRole
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)


class TryOnStatusEvent(BaseModel):
    """Append-only status transition event for a Try-On job."""

    model_config = ConfigDict(extra="forbid")

    status: TryOnJobStatus
    message: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=utc_now)


class TryOnCostEvent(BaseModel):
    """Sandbox cost event emitted by backend workflow ownership."""

    model_config = ConfigDict(extra="forbid")

    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    charge_status: TryOnChargeStatus = TryOnChargeStatus.NOT_CHARGED
    credits_charged: int = Field(default=0, ge=0)
    message: str = Field(default="Sandbox job was not charged.", min_length=1)
    occurred_at: datetime = Field(default_factory=utc_now)


class TryOnQualityCheck(BaseModel):
    """Single deterministic quality check result for a Try-On output."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class TryOnQualityReport(BaseModel):
    """Quality verifier report attached before a result is exposed."""

    model_config = ConfigDict(extra="forbid")

    passed: bool
    checks: list[TryOnQualityCheck] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class TryOnResultImage(BaseModel):
    """Public metadata for a generated Try-On result image."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)


class TryOnResult(BaseModel):
    """Completed Try-On result returned after quality verification."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    image: TryOnResultImage
    quality_report: TryOnQualityReport
    style_summary: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class TryOnError(BaseModel):
    """Structured Try-On error safe for API responses."""

    model_config = ConfigDict(extra="forbid")

    code: TryOnErrorCode
    message: str = Field(min_length=1)
    details: dict[str, JsonValue] = Field(default_factory=dict)


class TryOnJob(BaseModel):
    """Backend-owned aggregate for one Try-On sandbox job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    status: TryOnJobStatus
    inputs: list[TryOnInputMetadata] = Field(default_factory=list)
    status_events: list[TryOnStatusEvent] = Field(default_factory=list)
    cost_events: list[TryOnCostEvent] = Field(default_factory=list)
    quality_report: TryOnQualityReport | None = None
    result: TryOnResult | None = None
    error: TryOnError | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TryOnJobCreatedResponse(BaseModel):
    """API response returned when a Try-On job is accepted."""

    model_config = ConfigDict(extra="forbid")

    job: TryOnJob


class TryOnJobStatusResponse(BaseModel):
    """API response returned for Try-On status polling."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: TryOnWorkflowType = TryOnWorkflowType.TRY_ON
    status: TryOnJobStatus
    status_events: list[TryOnStatusEvent] = Field(default_factory=list)
    cost_events: list[TryOnCostEvent] = Field(default_factory=list)
    error: TryOnError | None = None


class TryOnResultResponse(BaseModel):
    """API response returned when a Try-On result is ready."""

    model_config = ConfigDict(extra="forbid")

    result: TryOnResult
    cost_events: list[TryOnCostEvent] = Field(default_factory=list)


class TryOnNotReadyResponse(BaseModel):
    """API response returned when a Try-On result is not available yet."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    status: TryOnJobStatus
    error: TryOnError


class TryOnErrorResponse(BaseModel):
    """API response wrapper for typed Try-On errors."""

    model_config = ConfigDict(extra="forbid")

    error: TryOnError
