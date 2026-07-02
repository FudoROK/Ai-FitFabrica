"""In-memory repository fallback for queue jobs and worker leases."""

from __future__ import annotations

from datetime import timedelta

from src.domain.operations import (
    QueueJobRecord,
    QueueJobStatus,
    WorkerLeaseRecord,
    WorkerLeaseStatus,
)


class InMemoryOperationsRepository:
    """Store queue jobs and worker leases in memory when SQL is unavailable."""

    def __init__(self) -> None:
        """Initialize in-memory queue job and lease stores."""
        self._jobs: dict[str, QueueJobRecord] = {}
        self._jobs_by_idempotency_key: dict[str, str] = {}
        self._leases: dict[str, WorkerLeaseRecord] = {}

    async def get_job_by_idempotency_key(self, *, idempotency_key: str) -> QueueJobRecord | None:
        """Return the in-memory queue job for the requested idempotency key."""
        job_id = self._jobs_by_idempotency_key.get(idempotency_key)
        return None if job_id is None else self._jobs.get(job_id)

    async def enqueue_job(
        self,
        *,
        workflow_type: str,
        workflow_reference: str,
        payload: dict[str, object],
        idempotency_key: str,
        max_attempts: int,
        now,
    ) -> QueueJobRecord:
        """Persist one in-memory queue job."""
        job = QueueJobRecord(
            job_id=f"queue_job_{len(self._jobs) + 1}",
            workflow_type=workflow_type,
            workflow_reference=workflow_reference,
            status=QueueJobStatus.QUEUED,
            idempotency_key=idempotency_key,
            payload=payload,
            attempt_count=0,
            max_attempts=max_attempts,
            last_error=None,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        self._jobs_by_idempotency_key[idempotency_key] = job.job_id
        return job

    async def get_job(self, *, job_id: str) -> QueueJobRecord | None:
        """Return the requested in-memory queue job."""
        return self._jobs.get(job_id)

    async def claim_stale_processing_job(self, *, stale_before, now) -> QueueJobRecord | None:
        """Return one stale processing job to queued state for worker recovery."""
        stale_jobs = sorted(
            (
                job
                for job in self._jobs.values()
                if job.status == QueueJobStatus.PROCESSING
                and job.updated_at <= stale_before
                and job.attempt_count < job.max_attempts
            ),
            key=lambda job: job.updated_at,
        )
        if not stale_jobs:
            return None
        job = stale_jobs[0]
        updated = job.model_copy(update={"status": QueueJobStatus.QUEUED, "updated_at": now})
        self._jobs[job.job_id] = updated
        return updated

    async def mark_job_processing(self, *, job_id: str, now) -> QueueJobRecord:
        """Mark the requested in-memory queue job as processing."""
        job = self._jobs[job_id]
        updated = job.model_copy(
            update={
                "status": QueueJobStatus.PROCESSING,
                "attempt_count": job.attempt_count + 1,
                "updated_at": now,
            }
        )
        self._jobs[job_id] = updated
        return updated

    async def mark_job_completed(self, *, job_id: str, now) -> QueueJobRecord:
        """Mark the requested in-memory queue job as completed."""
        job = self._jobs[job_id]
        updated = job.model_copy(update={"status": QueueJobStatus.COMPLETED, "updated_at": now})
        self._jobs[job_id] = updated
        return updated

    async def mark_job_failed(self, *, job_id: str, error_message: str, now) -> QueueJobRecord:
        """Mark the requested in-memory queue job as failed."""
        job = self._jobs[job_id]
        updated = job.model_copy(
            update={"status": QueueJobStatus.FAILED, "last_error": error_message, "updated_at": now}
        )
        self._jobs[job_id] = updated
        return updated

    async def acquire_lease(self, *, queue_job_id: str, worker_name: str, now, duration_seconds: int) -> WorkerLeaseRecord:
        """Acquire one in-memory worker lease."""
        lease = WorkerLeaseRecord(
            lease_id=f"lease_{queue_job_id}",
            queue_job_id=queue_job_id,
            worker_name=worker_name,
            status=WorkerLeaseStatus.ACTIVE,
            acquired_at=now,
            expires_at=now + timedelta(seconds=duration_seconds),
            released_at=None,
        )
        self._leases[lease.lease_id] = lease
        return lease

    async def renew_lease(self, *, lease_id: str, now, duration_seconds: int) -> WorkerLeaseRecord:
        """Renew one in-memory worker lease."""
        lease = self._leases[lease_id]
        updated = lease.model_copy(
            update={"status": WorkerLeaseStatus.ACTIVE, "expires_at": now + timedelta(seconds=duration_seconds)}
        )
        self._leases[lease_id] = updated
        return updated

    async def release_lease(self, *, lease_id: str, now) -> WorkerLeaseRecord:
        """Release one in-memory worker lease."""
        lease = self._leases[lease_id]
        updated = lease.model_copy(
            update={"status": WorkerLeaseStatus.RELEASED, "released_at": now}
        )
        self._leases[lease_id] = updated
        return updated

    async def count_jobs_by_status(self, *, status: str) -> int:
        """Return the number of in-memory queue jobs in the requested status."""
        return sum(1 for job in self._jobs.values() if job.status.value == status)
