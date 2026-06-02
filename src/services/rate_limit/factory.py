"""Rate limiter composition root + fail-mode policy."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from google.api_core.exceptions import GoogleAPIError

from src.adapters.cache.redis_client import build_redis_client
from ...settings import Settings
from .contracts import RateLimitDecision, RateLimiter
from .inmemory_rate_limiter import InMemoryRateLimiter
from .redis_rate_limiter import RedisRateLimiter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _UnavailableRateLimiter:
    """Fallback limiter that reports backend unavailability as an error decision."""

    reason: str

    def allow(self, key: str) -> RateLimitDecision:
        """Return a backend error decision for every key."""
        return RateLimitDecision(status="backend_error", reason=self.reason)


class FailModeRateLimiter:
    """Wrap a limiter and normalize backend failures into policy-driven decisions."""

    def __init__(self, *, limiter: RateLimiter, fail_mode: str = "closed") -> None:
        """Validate the fail mode and store the wrapped limiter."""
        normalized = (fail_mode or "closed").strip().lower()
        if normalized not in {"open", "closed"}:
            raise ValueError("rate_limit_fail_mode must be one of: open, closed")
        self._limiter = limiter
        self._fail_mode = normalized

    def allow(self, key: str) -> RateLimitDecision:
        """Delegate to the wrapped limiter and convert backend exceptions into decisions."""
        try:
            return self._limiter.allow(key)
        except GoogleAPIError:
            logger.error("RATE_LIMIT_BACKEND_FAILURE", extra={"rate_key": key, "fail_mode": self._fail_mode})
            return RateLimitDecision(status="backend_error", reason="rate_limiter_backend_failure")
        except Exception:
            logger.exception("RATE_LIMIT_BACKEND_FAILURE", extra={"rate_key": key, "fail_mode": self._fail_mode})
            return RateLimitDecision(status="backend_error", reason="rate_limiter_backend_failure")


def create_rate_limiter(
    settings: Settings,
    *,
    max_events: int | None = None,
    window_seconds: int | None = None,
    collection_name: str | None = None,
    backend_override: str | None = None,
) -> RateLimiter:
    """Create the configured rate limiter implementation for the current runtime."""
    resolved_max_events = int(max_events if max_events is not None else settings.rate_limit_max_events)
    resolved_window_seconds = int(window_seconds if window_seconds is not None else settings.rate_limit_window_seconds)
    resolved_collection_name = collection_name or settings.rate_limit_collection

    if backend_override is not None:
        backend = backend_override.strip().lower()
    elif not settings.enable_distributed_rate_limit:
        backend = "inmemory"
    else:
        backend = (settings.rate_limit_backend or "redis").strip().lower()

    if backend == "redis":
        limiter = RedisRateLimiter(
            redis_client=build_redis_client(settings),
            max_events=resolved_max_events,
            window_seconds=resolved_window_seconds,
            key_prefix=f"{settings.redis_key_prefix}:{resolved_collection_name}",
        )
    elif backend == "inmemory":
        limiter = InMemoryRateLimiter(
            max_events=resolved_max_events,
            window_seconds=resolved_window_seconds,
        )
    else:
        raise ValueError("Unsupported rate limit backend. Expected one of: redis, inmemory")

    return FailModeRateLimiter(limiter=limiter, fail_mode=settings.rate_limit_fail_mode)
