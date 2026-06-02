from __future__ import annotations

from types import SimpleNamespace

from src.services.rate_limit.factory import create_rate_limiter


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        enable_distributed_rate_limit=True,
        rate_limit_backend="redis",
        rate_limit_max_events=10,
        rate_limit_window_seconds=60,
        rate_limit_fail_mode="closed",
        rate_limit_collection="runtime_rate_limits",
        redis_url="redis://localhost:6379/0",
        redis_key_prefix="fitfabrica",
    )


def test_create_rate_limiter_builds_redis_backend(monkeypatch) -> None:
    monkeypatch.setattr("src.services.rate_limit.factory.build_redis_client", lambda settings: "redis-client")

    limiter = create_rate_limiter(_settings())

    assert limiter.__class__.__name__ == "FailModeRateLimiter"
