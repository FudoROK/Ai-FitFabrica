import time

from src.services.rate_limit import InMemoryRateLimiter


def test_rate_limiter_allows_until_limit_then_blocks():
    limiter = InMemoryRateLimiter(max_events=2, window_seconds=60)

    assert limiter.allow("lead-1").status == "allowed"
    assert limiter.allow("lead-1").status == "allowed"
    denied = limiter.allow("lead-1")

    assert denied.status == "denied_limit_exceeded"
    assert denied.remaining == 0
    assert denied.retry_after_seconds is not None


def test_rate_limiter_window_resets_after_expiry():
    limiter = InMemoryRateLimiter(max_events=1, window_seconds=1)

    assert limiter.allow("lead-2").status == "allowed"
    assert limiter.allow("lead-2").status == "denied_limit_exceeded"

    time.sleep(1.05)

    assert limiter.allow("lead-2").status == "allowed"
