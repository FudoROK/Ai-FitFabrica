"""Portable worker execution loop for durable queue jobs."""

from __future__ import annotations

from datetime import timedelta

from src.domain.operations import WorkerCycleResult


class WorkerRuntime:
    """Claim queue jobs, run handlers, and record durable completion state."""

    def __init__(
        self,
        *,
        queue,
        repository,
        lease_service,
        handlers: dict[str, object],
        worker_name: str,
        clock,
        stale_reclaim_seconds: int = 300,
    ) -> None:
        """Store runtime queue, repository, lease, and handler dependencies."""
        self._queue = queue
        self._repository = repository
        self._lease_service = lease_service
        self._handlers = handlers
        self._worker_name = worker_name
        self._clock = clock
        self._stale_reclaim_seconds = stale_reclaim_seconds

    async def run_one_cycle(self) -> WorkerCycleResult:
        """Run one worker cycle against the active portable queue backend."""
        claimed_job_id = await self._queue.claim_next()
        job = None
        if claimed_job_id is None:
            job = await self._claim_stale_processing_job()
            claimed_job_id = job.job_id if job is not None else None
        if claimed_job_id is None and job is None:
            return WorkerCycleResult()

        if job is None:
            job = await self._repository.get_job(job_id=claimed_job_id)
        if job is None:
            return WorkerCycleResult(claimed_job_id=claimed_job_id, skipped_jobs=1)

        await self._repository.mark_job_processing(job_id=job.job_id, now=self._clock())
        lease = await self._lease_service.acquire(queue_job_id=job.job_id, worker_name=self._worker_name)
        handler = self._handlers.get(job.workflow_type)
        if handler is None:
            await self._repository.mark_job_failed(
                job_id=job.job_id,
                error_message=f"missing_handler:{job.workflow_type}",
                now=self._clock(),
            )
            await self._lease_service.release(lease_id=lease.lease_id)
            return WorkerCycleResult(claimed_job_id=job.job_id, failed_jobs=1)

        try:
            await handler(job)
        except Exception as exc:
            await self._repository.mark_job_failed(job_id=job.job_id, error_message=str(exc), now=self._clock())
            await self._lease_service.release(lease_id=lease.lease_id)
            return WorkerCycleResult(claimed_job_id=job.job_id, failed_jobs=1)

        await self._repository.mark_job_completed(job_id=job.job_id, now=self._clock())
        await self._lease_service.release(lease_id=lease.lease_id)
        return WorkerCycleResult(claimed_job_id=job.job_id, completed_jobs=1)

    async def _claim_stale_processing_job(self):
        """Recover one stale SQL processing job when the queue lost its item."""
        now = self._clock()
        stale_before = now - timedelta(seconds=self._stale_reclaim_seconds)
        return await self._repository.claim_stale_processing_job(stale_before=stale_before, now=now)
