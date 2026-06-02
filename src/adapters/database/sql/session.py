"""Async SQLAlchemy session factory helpers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def build_session_factory(engine):
    """Create a non-expiring async session factory for runtime repositories."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
