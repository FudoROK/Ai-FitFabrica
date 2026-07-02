from __future__ import annotations

from src.services.rate_limit import FailModeRateLimiter, RateLimitDecision


class _BrokenLimiter:
    def allow(self, key: str) -> RateLimitDecision:
        raise RuntimeError(f"broken limiter for {key}")


class _AllowLimiter:
    def allow(self, key: str) -> RateLimitDecision:
        return RateLimitDecision(status="allowed")


def test_rate_limiter_fail_open_on_backend_failure():
    limiter = FailModeRateLimiter(limiter=_BrokenLimiter(), fail_mode="open")

    decision = limiter.allow("lead-fail-open")

    assert decision.status == "backend_error"
    assert decision.reason == "rate_limiter_backend_failure"


def test_rate_limiter_fail_closed_on_backend_failure():
    limiter = FailModeRateLimiter(limiter=_BrokenLimiter(), fail_mode="closed")

    decision = limiter.allow("lead-fail-closed")

    assert decision.status == "backend_error"
    assert decision.reason == "rate_limiter_backend_failure"


def test_rate_limiter_defaults_to_fail_closed_on_backend_failure():
    limiter = FailModeRateLimiter(limiter=_BrokenLimiter())

    decision = limiter.allow("lead-default-fail-closed")

    assert decision.status == "backend_error"
    assert decision.reason == "rate_limiter_backend_failure"
