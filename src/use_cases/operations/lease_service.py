"""Reusable worker lease orchestration for portable queue jobs."""

from __future__ import annotations

from src.domain.operations import WorkerLeaseRecord
from src.use_cases.operations.ports import OperationsRepositoryPort


class WorkerLeaseService:
    """Acquire, renew, and release worker leases through the durable repository."""

    def __init__(
        self,
        *,
        repository: OperationsRepositoryPort,
        clock,
        lease_duration_seconds: int,
    ) -> None:
        """Store the repository and lease configuration."""
        self._repository = repository
        self._clock = clock
        self._lease_duration_seconds = lease_duration_seconds

    async def acquire(self, *, queue_job_id: str, worker_name: str) -> WorkerLeaseRecord:
        """Acquire one worker lease for the requested queue job."""
        return await self._repository.acquire_lease(
            queue_job_id=queue_job_id,
            worker_name=worker_name,
            now=self._clock(),
            duration_seconds=self._lease_duration_seconds,
        )

    async def renew(self, *, lease_id: str) -> WorkerLeaseRecord:
        """Renew one existing worker lease."""
        return await self._repository.renew_lease(
            lease_id=lease_id,
            now=self._clock(),
            duration_seconds=self._lease_duration_seconds,
        )

    async def release(self, *, lease_id: str) -> WorkerLeaseRecord:
        """Release one existing worker lease."""
        return await self._repository.release_lease(lease_id=lease_id, now=self._clock())
