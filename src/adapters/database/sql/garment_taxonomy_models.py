"""SQLAlchemy models for garment taxonomy and wear-control governance."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class GarmentTaxonomyItemRow(SqlBase):
    """Approved garment taxonomy item or category."""

    __tablename__ = "garment_taxonomy_items"

    code: Mapped[str] = mapped_column(String(96), primary_key=True)
    parent_code: Mapped[str | None] = mapped_column(ForeignKey("garment_taxonomy_items.code", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(96), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GarmentWearControlRow(SqlBase):
    """Approved way-of-wearing control scoped to an item or category."""

    __tablename__ = "garment_wear_controls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    taxonomy_item_code: Mapped[str | None] = mapped_column(ForeignKey("garment_taxonomy_items.code", ondelete="CASCADE"), index=True, nullable=True)
    parent_category_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    control_code: Mapped[str] = mapped_column(String(96), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instruction_template: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    default_for_auto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class GarmentTaxonomyCandidateRow(SqlBase):
    """AI-proposed garment taxonomy candidate waiting for human review."""

    __tablename__ = "garment_taxonomy_candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    proposed_code: Mapped[str] = mapped_column(String(96), index=True, nullable=False)
    proposed_display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    proposed_parent_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    proposed_category: Mapped[str] = mapped_column(String(96), nullable=False)
    proposed_controls_json: Mapped[list[str]] = mapped_column("proposed_controls", JSON, nullable=False, default=list)
    source_job_ids_json: Mapped[list[str]] = mapped_column("source_job_ids", JSON, nullable=False, default=list)
    examples_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    agent_reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_catalog_item_code: Mapped[str | None] = mapped_column(ForeignKey("garment_taxonomy_items.code", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GarmentTaxonomyAuditLogRow(SqlBase):
    """Audit log for taxonomy mutations."""

    __tablename__ = "garment_taxonomy_audit_log"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    before_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    after_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

