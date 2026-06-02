"""Backend-owned workflow dispatch logic for portable queue execution."""

from __future__ import annotations

from src.domain.operations import QueueJobRecord
from src.use_cases.operations.ports import OperationsRepositoryPort, QueuePublisherPort


class WorkflowDispatchService:
    """Enqueue idempotent workflow jobs into the portable queue contour."""

    def __init__(
        self,
        *,
        repository: OperationsRepositoryPort,
        queue: QueuePublisherPort,
        clock,
    ) -> None:
        """Store explicit queue, repository, and time dependencies."""
        self._repository = repository
        self._queue = queue
        self._clock = clock

    async def enqueue_workflow(
        self,
        *,
        workflow_type: str,
        workflow_reference: str,
        payload: dict[str, object],
        idempotency_key: str,
        max_attempts: int = 3,
    ) -> QueueJobRecord:
        """Persist and publish one idempotent workflow queue job."""
        existing = await self._repository.get_job_by_idempotency_key(idempotency_key=idempotency_key)
        if existing is not None:
            return existing

        job = await self._repository.enqueue_job(
            workflow_type=workflow_type,
            workflow_reference=workflow_reference,
            payload=payload,
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
            now=self._clock(),
        )
        await self._queue.publish(job_id=job.job_id)
        return job
