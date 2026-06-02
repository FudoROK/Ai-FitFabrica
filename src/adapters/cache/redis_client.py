"""Redis client bootstrap helpers."""

from __future__ import annotations

import importlib


def build_redis_client(settings):
    """Build the shared Redis client from validated runtime settings."""
    if not settings.redis_url:
        raise ValueError("redis_url is required to build the Redis client")
    try:
        redis = importlib.import_module("redis")
    except ModuleNotFoundError as exc:
        raise RuntimeError("redis is required when redis-backed runtime infrastructure is configured") from exc
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
