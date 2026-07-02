"""Portable SQL model definitions."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase
from .similar_search_models import SimilarSearchClickEventRow  # noqa: F401


class PortableRuntimeMetadataRow(SqlBase):
    """Minimal metadata table for portable runtime bootstrap state."""

    __tablename__ = "portable_runtime_metadata"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
