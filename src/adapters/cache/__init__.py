"""Portable cache adapters."""

__all__ = ["build_redis_client"]


def __getattr__(name: str):
    """Load optional cache adapters lazily to avoid import-time dependency failures."""
    if name == "build_redis_client":
        from .redis_client import build_redis_client

        return build_redis_client
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
