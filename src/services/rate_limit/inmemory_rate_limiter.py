"""In-memory rate limiter for local/dev and tests."""
from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from .contracts import RateLimitDecision


class InMemoryRateLimiter:
    def __init__(self, *, max_events: int, window_seconds: int) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> RateLimitDecision:
        now = monotonic()
        window_start = now - self.window_seconds
        with self._lock:
            queue = self._events[key]
            while queue and queue[0] < window_start:
                queue.popleft()
            if len(queue) >= self.max_events:
                retry_after_seconds = int(max(queue[0] + self.window_seconds - now, 1)) if queue else None
                return RateLimitDecision(
                    status="denied_limit_exceeded",
                    remaining=0,
                    retry_after_seconds=retry_after_seconds,
                    reason="rate_limit_exceeded",
                )
            queue.append(now)
            remaining = max(self.max_events - len(queue), 0)
            return RateLimitDecision(status="allowed", remaining=remaining)
