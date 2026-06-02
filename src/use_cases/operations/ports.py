"""Ports for portable queue, worker, and operations orchestration."""

from __future__ import annotations

from typing import Protocol

from src.domain.operations import OperationsHealthSnapshot, QueueJobRecord, WorkerLeaseRecord


class QueuePublisherPort(Protocol):
    """Publish and claim queue job identifiers from the active queue backend."""

    async def publish(self, *, job_id: str) -> None:
        """Publish one durable queue job identifier to the backend queue."""

    async def claim_next(self) -> str | None:
        """Claim the next available durable queue job identifier."""


class OperationsRepositoryPort(Protocol):
    """Persistence contract for queue jobs and worker leases."""

    async def get_job_by_idempotency_key(self, *, idempotency_key: str) -> QueueJobRecord | None:
        """Return the durable queue job matching the requested idempotency key."""

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
        """Persist one durable queue job in queued state."""

    async def get_job(self, *, job_id: str) -> QueueJobRecord | None:
        """Return the durable queue job for the requested identifier."""

    async def mark_job_processing(self, *, job_id: str, now) -> QueueJobRecord:
        """Mark the requested queue job as processing and increment its attempts."""

    async def mark_job_completed(self, *, job_id: str, now) -> QueueJobRecord:
        """Mark the requested queue job as completed."""

    async def mark_job_failed(self, *, job_id: str, error_message: str, now) -> QueueJobRecord:
        """Mark the requested queue job as failed and store the latest error."""

    async def acquire_lease(self, *, queue_job_id: str, worker_name: str, now, duration_seconds: int) -> WorkerLeaseRecord:
        """Acquire one active worker lease for the requested queue job."""

    async def renew_lease(self, *, lease_id: str, now, duration_seconds: int) -> WorkerLeaseRecord:
        """Renew one active worker lease."""

    async def release_lease(self, *, lease_id: str, now) -> WorkerLeaseRecord:
        """Release one active worker lease."""

    async def count_jobs_by_status(self, *, status: str) -> int:
        """Return the number of durable queue jobs in the requested state."""


class OperationsHealthPort(Protocol):
    """Expose a portable operations health snapshot."""

    async def snapshot(self) -> OperationsHealthSnapshot:
        """Return the current queue and worker health snapshot."""
