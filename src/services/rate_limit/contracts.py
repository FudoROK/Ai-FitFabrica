"""Rate limiting contracts and decisions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, TypeVar


from typing import Literal

@dataclass(frozen=True)
class RateLimitDecision:
    status: Literal["allowed", "denied_limit_exceeded", "backend_error"]
    remaining: int | None = None
    retry_after_seconds: int | None = None
    reason: str | None = None


class RateLimiter(Protocol):
    def allow(self, key: str) -> RateLimitDecision:
        """Return whether a request for key is allowed in the current window."""


T = TypeVar("T")


class TransactionRunner(Protocol):
    def __call__(self, client: Any, work: Callable[[Any], T]) -> T:
        """Execute callback inside backend-specific transaction lifecycle."""
