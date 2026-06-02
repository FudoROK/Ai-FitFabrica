"""Serialization helpers for operations SQL rows and domain models."""

from __future__ import annotations

from src.domain.operations import QueueJobRecord, QueueJobStatus, WorkerLeaseRecord, WorkerLeaseStatus

from .operations_models import QueueJobRow, WorkerLeaseRow


def queue_job_from_row(row: QueueJobRow) -> QueueJobRecord:
    """Convert one queue job row into the domain model."""
    return QueueJobRecord(
        job_id=row.queue_job_id,
        workflow_type=row.workflow_type,
        workflow_reference=row.workflow_reference,
        status=QueueJobStatus(row.status),
        idempotency_key=row.idempotency_key,
        payload=dict(row.payload_json or {}),
        attempt_count=row.attempt_count,
        max_attempts=row.max_attempts,
        last_error=row.last_error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def worker_lease_from_row(row: WorkerLeaseRow) -> WorkerLeaseRecord:
    """Convert one worker lease row into the domain model."""
    return WorkerLeaseRecord(
        lease_id=row.lease_id,
        queue_job_id=row.queue_job_id,
        worker_name=row.worker_name,
        status=WorkerLeaseStatus(row.status),
        acquired_at=row.acquired_at,
        expires_at=row.expires_at,
        released_at=row.released_at,
    )
