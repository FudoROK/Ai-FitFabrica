"""Redis-backed queue for portable worker execution."""

from __future__ import annotations


class RedisQueue:
    """Publish and claim queue job identifiers through Redis list primitives."""

    def __init__(self, *, redis_client, queue_name: str) -> None:
        """Store the shared Redis client and queue key."""
        self._redis = redis_client
        self._queue_name = queue_name

    async def publish(self, *, job_id: str) -> None:
        """Publish one queue job identifier to Redis."""
        self._redis.rpush(self._queue_name, job_id)

    async def claim_next(self) -> str | None:
        """Claim the next queued job identifier from Redis."""
        return self._redis.lpop(self._queue_name)
