"""In-memory Try-On job repository adapter."""
from __future__ import annotations

import asyncio

from src.domain.try_on import TryOnJob
from src.use_cases.try_on.ports import TryOnJobRepositoryPort


class InMemoryTryOnJobRepository(TryOnJobRepositoryPort):
    """Non-durable job storage; jobs disappear after the backend process restarts."""

    def __init__(self) -> None:
        """Initialize an empty in-process job store."""
        self._lock = asyncio.Lock()
        self._jobs: dict[str, TryOnJob] = {}

    async def save(self, job: TryOnJob) -> None:
        """Save or replace a job in the in-memory store."""
        async with self._lock:
            self._jobs[job.job_id] = job

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a saved job by identifier, if present."""
        async with self._lock:
            return self._jobs.get(job_id)
