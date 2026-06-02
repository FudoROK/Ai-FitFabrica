"""Portable SQLAlchemy models for pricing workflow persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class PricingJobRow(SqlBase):
    """Canonical pricing job aggregate root row."""

    __tablename__ = "pricing_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    desired_margin_percent: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PricingRecommendationRow(SqlBase):
    """Persisted pricing recommendation bound to one pricing job."""

    __tablename__ = "pricing_recommendations"

    recommendation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("pricing_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    recommended_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    market_min: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    market_avg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    market_max: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_pricing_jobs_status_created_at", PricingJobRow.status, PricingJobRow.created_at)
