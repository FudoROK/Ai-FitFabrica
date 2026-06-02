from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.adapters.operations.in_memory_repository import InMemoryOperationsRepository
from src.adapters.queue.in_memory_queue import InMemoryQueue
from src.use_cases.operations.dispatch_service import WorkflowDispatchService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_dispatch_service_enqueues_one_idempotent_job() -> None:
    repository = InMemoryOperationsRepository()
    queue = InMemoryQueue()
    service = WorkflowDispatchService(repository=repository, queue=queue, clock=_utc_now)

    first = await service.enqueue_workflow(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
    )
    second = await service.enqueue_workflow(
        workflow_type="try_on",
        workflow_reference="job-1",
        payload={"job_id": "job-1"},
        idempotency_key="try_on:job-1",
    )

    assert first.job_id == second.job_id
