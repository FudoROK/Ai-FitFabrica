"""Rate limiter composition root + fail-mode policy."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from google.api_core.exceptions import GoogleAPIError

from src.adapters.database.firestore.storage_primitives import get_firestore_client, run_in_transaction_with_client
from ...settings import Settings
from .contracts import RateLimitDecision, RateLimiter
from .firestore_rate_limiter import FirestoreRateLimiter
from .inmemory_rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _UnavailableRateLimiter:
    reason: str

    def allow(self, key: str) -> RateLimitDecision:
        # An unavailable limiter is equivalent to a backend error for decision purposes
        return RateLimitDecision(status="backend_error", reason=self.reason)


class FailModeRateLimiter:
    def __init__(self, *, limiter: RateLimiter, fail_mode: str = "closed") -> None:
        normalized = (fail_mode or "closed").strip().lower()
        if normalized not in {"open", "closed"}:
            raise ValueError("rate_limit_fail_mode must be one of: open, closed")
        self._limiter = limiter
        self._fail_mode = normalized

    def allow(self, key: str) -> RateLimitDecision:
        try:
            return self._limiter.allow(key)
        except GoogleAPIError: # Catch specific Firestore backend errors
            logger.error("RATE_LIMIT_BACKEND_FAILURE", extra={"rate_key": key, "fail_mode": self._fail_mode})
            return RateLimitDecision(status="backend_error", reason="rate_limiter_backend_failure")
        except Exception: # Catch other unexpected errors and treat them as backend errors
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
    resolved_max_events = int(max_events if max_events is not None else settings.rate_limit_max_events)
    resolved_window_seconds = int(window_seconds if window_seconds is not None else settings.rate_limit_window_seconds)
    resolved_collection_name = collection_name or settings.rate_limit_collection

    if backend_override is not None:
        backend = backend_override.strip().lower()
    elif not settings.enable_distributed_rate_limit:
        backend = "inmemory"
    else:
        backend = (settings.rate_limit_backend or "firestore").strip().lower()

    if backend == "firestore":
        firestore_client = get_firestore_client()
        if firestore_client is None:
            limiter: RateLimiter = _UnavailableRateLimiter("Firestore rate limiter backend is unavailable")
        else:
            limiter = FirestoreRateLimiter(
                firestore_client=firestore_client,
                max_events=resolved_max_events,
                window_seconds=resolved_window_seconds,
                collection_name=resolved_collection_name,
                transaction_runner=run_in_transaction_with_client,
            )
    elif backend == "inmemory":
        limiter = InMemoryRateLimiter(
            max_events=resolved_max_events,
            window_seconds=resolved_window_seconds,
        )
    else:
        raise ValueError("Unsupported rate limit backend. Expected one of: firestore, inmemory")

    return FailModeRateLimiter(limiter=limiter, fail_mode=settings.rate_limit_fail_mode)
