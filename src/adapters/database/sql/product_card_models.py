"""Portable SQLAlchemy models for product-card workflow persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class ProductCardJobRow(SqlBase):
    """Canonical product-card job aggregate root row."""

    __tablename__ = "product_card_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    target_channel: Mapped[str] = mapped_column(String(64), nullable=False)
    brand_tone: Mapped[str] = mapped_column(String(128), nullable=False)
    title_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductCardSourceAssetRow(SqlBase):
    """Stored source asset reference bound to one product-card job."""

    __tablename__ = "product_card_source_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("product_card_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductCardVersionRow(SqlBase):
    """Generated product-card version stored separately from the job root."""

    __tablename__ = "product_card_versions"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("product_card_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    bullet_points_json: Mapped[list[str]] = mapped_column("bullet_points", JSON, nullable=False, default=list)
    attributes_json: Mapped[dict[str, str]] = mapped_column("attributes", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductCardQualityNoteRow(SqlBase):
    """Quality note captured for one generated product-card version."""

    __tablename__ = "product_card_quality_notes"

    note_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("product_card_versions.version_id", ondelete="CASCADE"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_product_card_jobs_status_created_at", ProductCardJobRow.status, ProductCardJobRow.created_at)
Index("ix_product_card_versions_job_id_created_at", ProductCardVersionRow.job_id, ProductCardVersionRow.created_at)
