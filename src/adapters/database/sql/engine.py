"""Async SQLAlchemy engine construction."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def build_async_engine(settings) -> AsyncEngine:
    """Build the shared PostgreSQL async engine from validated settings."""
    if not settings.postgres_dsn:
        raise ValueError("postgres_dsn is required to build the PostgreSQL engine")
    return create_async_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
        pool_timeout=settings.postgres_pool_timeout_seconds,
    )
