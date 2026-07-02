from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.adapters.operations.in_memory_repository import InMemoryOperationsRepository
from src.adapters.queue.in_memory_queue import InMemoryQueue
from src.services.workers.worker_runtime import WorkerRuntime
from src.use_cases.operations.lease_service import WorkerLeaseService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_worker_runtime_marks_job_completed_after_handler_success() -> None:
    repository = InMemoryOperationsRepository()
    queue = InMemoryQueue()
    job = await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=_utc_now(),
    )
    await queue.publish(job_id=job.job_id)
    runtime = WorkerRuntime(
        queue=queue,
        repository=repository,
        lease_service=WorkerLeaseService(repository=repository, clock=_utc_now, lease_duration_seconds=300),
        handlers={"try_on": _handler_success},
        worker_name="portable-worker",
        clock=_utc_now,
    )

    result = await runtime.run_one_cycle()
    saved = await repository.get_job(job_id=job.job_id)

    assert result.completed_jobs == 1
    assert saved is not None
    assert saved.status.value == "completed"


@pytest.mark.asyncio
async def test_worker_runtime_marks_job_failed_when_handler_raises() -> None:
    repository = InMemoryOperationsRepository()
    queue = InMemoryQueue()
    job = await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=_utc_now(),
    )
    await queue.publish(job_id=job.job_id)
    runtime = WorkerRuntime(
        queue=queue,
        repository=repository,
        lease_service=WorkerLeaseService(repository=repository, clock=_utc_now, lease_duration_seconds=300),
        handlers={"try_on": _handler_failure},
        worker_name="portable-worker",
        clock=_utc_now,
    )

    result = await runtime.run_one_cycle()
    saved = await repository.get_job(job_id=job.job_id)

    assert result.failed_jobs == 1
    assert saved is not None
    assert saved.status.value == "failed"


@pytest.mark.asyncio
async def test_worker_runtime_reclaims_stale_processing_job_when_queue_is_empty() -> None:
    stale_now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    repository = InMemoryOperationsRepository()
    queue = InMemoryQueue()
    job = await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=stale_now - timedelta(minutes=10),
    )
    await repository.mark_job_processing(job_id=job.job_id, now=stale_now - timedelta(minutes=10))
    runtime = WorkerRuntime(
        queue=queue,
        repository=repository,
        lease_service=WorkerLeaseService(repository=repository, clock=lambda: stale_now, lease_duration_seconds=300),
        handlers={"try_on": _handler_success},
        worker_name="portable-worker",
        clock=lambda: stale_now,
        stale_reclaim_seconds=300,
    )

    result = await runtime.run_one_cycle()
    saved = await repository.get_job(job_id=job.job_id)

    assert result.completed_jobs == 1
    assert result.claimed_job_id == job.job_id
    assert saved is not None
    assert saved.status.value == "completed"


async def _handler_success(_job) -> None:
    return None


async def _handler_failure(_job) -> None:
    raise RuntimeError("boom")
