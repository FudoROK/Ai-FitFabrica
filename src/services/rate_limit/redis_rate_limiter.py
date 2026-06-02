"""Redis-backed distributed rate limiter."""

from __future__ import annotations

import time

from .contracts import RateLimitDecision


class RedisRateLimiter:
    """Sliding-window rate limiter implemented with Redis sorted sets."""

    def __init__(self, *, redis_client, max_events: int, window_seconds: int, key_prefix: str) -> None:
        """Store Redis dependencies and window configuration."""
        self._redis = redis_client
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._key_prefix = key_prefix

    def allow(self, key: str) -> RateLimitDecision:
        """Evaluate whether the given key stays within the configured window."""
        now_seconds = int(time.time())
        now_member = str(time.time_ns())
        bucket_key = f"{self._key_prefix}:{key}"
        window_start = now_seconds - self._window_seconds

        pipeline = self._redis.pipeline()
        pipeline.zremrangebyscore(bucket_key, 0, window_start)
        pipeline.zcard(bucket_key)
        _, current_count = pipeline.execute()

        if int(current_count) >= self._max_events:
            return RateLimitDecision(
                status="denied_limit_exceeded",
                remaining=0,
                retry_after_seconds=self._window_seconds,
                reason="rate_limit_exceeded",
            )

        pipeline = self._redis.pipeline()
        pipeline.zadd(bucket_key, {now_member: now_seconds})
        pipeline.expire(bucket_key, self._window_seconds)
        pipeline.execute()

        remaining = max(self._max_events - int(current_count) - 1, 0)
        return RateLimitDecision(status="allowed", remaining=remaining)
