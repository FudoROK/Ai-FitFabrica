"""Typed domain models for portable queue and worker operations."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def operations_utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp for operations records."""
    return datetime.now(timezone.utc)


class QueueJobStatus(StrEnum):
    """Supported durable queue job states."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkerLeaseStatus(StrEnum):
    """Supported worker lease states."""

    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class QueueJobRecord(BaseModel):
    """Durable workflow queue job metadata."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: str = Field(min_length=1)
    workflow_reference: str = Field(min_length=1)
    status: QueueJobStatus
    idempotency_key: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    last_error: str | None = None
    created_at: datetime = Field(default_factory=operations_utc_now)
    updated_at: datetime = Field(default_factory=operations_utc_now)


class WorkerLeaseRecord(BaseModel):
    """Durable worker claim metadata bound to one queue job."""

    model_config = ConfigDict(extra="forbid")

    lease_id: str = Field(min_length=1)
    queue_job_id: str = Field(min_length=1)
    worker_name: str = Field(min_length=1)
    status: WorkerLeaseStatus
    acquired_at: datetime = Field(default_factory=operations_utc_now)
    expires_at: datetime
    released_at: datetime | None = None


class WorkerCycleResult(BaseModel):
    """Result summary for one worker execution cycle."""

    model_config = ConfigDict(extra="forbid")

    claimed_job_id: str | None = None
    completed_jobs: int = Field(default=0, ge=0)
    failed_jobs: int = Field(default=0, ge=0)
    skipped_jobs: int = Field(default=0, ge=0)


class OperationsHealthSnapshot(BaseModel):
    """Aggregated runtime health snapshot for queue and worker contours."""

    model_config = ConfigDict(extra="forbid")

    queue_backend: str = Field(min_length=1)
    queue_depth: int = Field(ge=0)
    worker_name: str = Field(min_length=1)
    redis_status: str = Field(min_length=1)
    postgres_status: str = Field(min_length=1)
