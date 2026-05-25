"""Ports for Try-On workflow persistence and generation."""
from __future__ import annotations

from typing import Protocol

from src.domain.try_on import TryOnInputMetadata, TryOnJob, TryOnResult


class TryOnJobRepositoryPort(Protocol):
    """Persistence boundary for Try-On job aggregates."""

    async def save(self, job: TryOnJob) -> None:
        """Persist the latest state of a Try-On job."""
        ...

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a Try-On job by identifier, if it exists."""
        ...


class TryOnGenerationPort(Protocol):
    """Generation boundary used by the workflow service."""

    async def generate(self, *, job_id: str, input_metadata: list[TryOnInputMetadata]) -> TryOnResult:
        """Generate a Try-On result for validated input metadata."""
        ...
