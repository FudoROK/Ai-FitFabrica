from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.adapters.operations.in_memory_repository import InMemoryOperationsRepository
from src.use_cases.operations.lease_service import WorkerLeaseService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_lease_service_renews_active_lease() -> None:
    repository = InMemoryOperationsRepository()
    await repository.enqueue_job(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
        max_attempts=3,
        now=_utc_now(),
    )
    service = WorkerLeaseService(repository=repository, clock=_utc_now, lease_duration_seconds=300)

    lease = await service.acquire(queue_job_id="queue_job_1", worker_name="portable-worker")
    renewed = await service.renew(lease_id=lease.lease_id)

    assert renewed.status.value == "active"
