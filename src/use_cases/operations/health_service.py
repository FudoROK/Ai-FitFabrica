"""Aggregate queue and worker readiness for operational status surfaces."""

from __future__ import annotations

from src.domain.operations import OperationsHealthSnapshot
from src.use_cases.operations.ports import OperationsRepositoryPort


class OperationsHealthService:
    """Build a portable operations health snapshot from runtime dependencies."""

    def __init__(
        self,
        *,
        repository: OperationsRepositoryPort,
        queue_backend: str,
        worker_name: str,
        postgres_configured: bool,
        redis_configured: bool,
    ) -> None:
        """Store repository-backed queue metrics and runtime component identity."""
        self._repository = repository
        self._queue_backend = queue_backend
        self._worker_name = worker_name
        self._postgres_configured = postgres_configured
        self._redis_configured = redis_configured

    async def snapshot(self) -> OperationsHealthSnapshot:
        """Return a current operations health snapshot for queue and worker readiness."""
        queue_depth = await self._repository.count_jobs_by_status(status="queued")
        return OperationsHealthSnapshot(
            queue_backend=self._queue_backend,
            queue_depth=queue_depth,
            worker_name=self._worker_name,
            redis_status="configured" if self._redis_configured else "not_configured",
            postgres_status="configured" if self._postgres_configured else "not_configured",
        )
