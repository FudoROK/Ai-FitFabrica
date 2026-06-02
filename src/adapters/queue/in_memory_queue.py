"""Deterministic in-memory queue for local and test runtime execution."""

from __future__ import annotations

from collections import deque


class InMemoryQueue:
    """Publish and claim queue job identifiers in memory."""

    def __init__(self) -> None:
        """Initialize the in-memory queue buffer."""
        self._items: deque[str] = deque()

    async def publish(self, *, job_id: str) -> None:
        """Publish one queue job identifier."""
        self._items.append(job_id)

    async def claim_next(self) -> str | None:
        """Claim the next queued job identifier."""
        return self._items.popleft() if self._items else None
