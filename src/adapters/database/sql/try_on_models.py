"""Portable SQLAlchemy models for Try-On workflow persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class TryOnJobRow(SqlBase):
    """Canonical Try-On job aggregate root row."""

    __tablename__ = "try_on_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(32), nullable=False)
    generation_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_metadata_json: Mapped[list[dict[str, object]]] = mapped_column("input_metadata", JSON, nullable=False, default=list)
    wear_control_selections_json: Mapped[list[dict[str, object]]] = mapped_column("wear_control_selections", JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnStoredInputRow(SqlBase):
    """Stored upload reference bound to one Try-On job."""

    __tablename__ = "try_on_stored_inputs"
    __table_args__ = (UniqueConstraint("job_id", "position", name="uq_try_on_stored_inputs_job_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(32), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    bucket_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnHumanIdentityAnalysisRow(SqlBase):
    """Validated Human Identity analysis bound one-to-one to a Try-On job."""

    __tablename__ = "try_on_human_identity_analyses"

    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), primary_key=True)
    invocation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    prompt_version: Mapped[str] = mapped_column(String(128), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(128), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    uncertainty_level: Mapped[str] = mapped_column(String(32), nullable=False)
    analysis_json: Mapped[dict[str, object]] = mapped_column("analysis", JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnGarmentIdentityAnalysisRow(SqlBase):
    """Validated Garment Identity analysis bound one-to-one to a Try-On job."""

    __tablename__ = "try_on_garment_identity_analyses"

    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), primary_key=True)
    invocation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    uncertainty_level: Mapped[str] = mapped_column(String(32), nullable=False)
    analysis_json: Mapped[dict[str, object]] = mapped_column("analysis", JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnGarmentSlotIdentityAnalysisRow(SqlBase):
    """Validated Garment Identity analysis bound to one outfit garment slot."""

    __tablename__ = "try_on_garment_slot_identity_analyses"
    __table_args__ = (UniqueConstraint("job_id", "slot_role", name="uq_try_on_garment_slot_identity_job_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_role: Mapped[str] = mapped_column(String(64), nullable=False)
    invocation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    uncertainty_level: Mapped[str] = mapped_column(String(32), nullable=False)
    analysis_json: Mapped[dict[str, object]] = mapped_column("analysis", JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnMaterialTextureAnalysisRow(SqlBase):
    """Validated Material / Texture analysis bound one-to-one to a Try-On job."""

    __tablename__ = "try_on_material_texture_analyses"

    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), primary_key=True)
    invocation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    uncertainty_level: Mapped[str] = mapped_column(String(32), nullable=False)
    analysis_json: Mapped[dict[str, object]] = mapped_column("analysis", JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnInstructionRow(SqlBase):
    """Validated generation instruction bound one-to-one to a Try-On job."""

    __tablename__ = "try_on_instructions"

    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), primary_key=True)
    invocation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    uncertainty_level: Mapped[str] = mapped_column(String(32), nullable=False)
    instruction_json: Mapped[dict[str, object]] = mapped_column("instruction", JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnStatusEventRow(SqlBase):
    """Append-only status event row for Try-On jobs."""

    __tablename__ = "try_on_status_events"
    __table_args__ = (UniqueConstraint("job_id", "position", name="uq_try_on_status_events_job_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnCostEventRow(SqlBase):
    """Recorded cost event row for Try-On jobs."""

    __tablename__ = "try_on_cost_events"
    __table_args__ = (UniqueConstraint("job_id", "position", name="uq_try_on_cost_events_job_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    estimated_units: Mapped[int] = mapped_column(Integer, nullable=False)
    charge_status: Mapped[str] = mapped_column(String(32), nullable=False)
    charged_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnResultRow(SqlBase):
    """Completed result payload stored separately from the job root."""

    __tablename__ = "try_on_results"

    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), primary_key=True)
    result_image_json: Mapped[dict[str, object]] = mapped_column("result_image", JSON, nullable=False)
    quality_report_json: Mapped[dict[str, object]] = mapped_column("quality_report", JSON, nullable=False)
    stylist_note: Mapped[str] = mapped_column(Text, nullable=False)
    input_metadata_json: Mapped[list[dict[str, object]]] = mapped_column("input_metadata", JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TryOnErrorRow(SqlBase):
    """Structured error payload stored when a job fails."""

    __tablename__ = "try_on_errors"

    job_id: Mapped[str] = mapped_column(ForeignKey("try_on_jobs.job_id", ondelete="CASCADE"), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict[str, object]] = mapped_column("details", JSON, nullable=False)


Index("ix_try_on_jobs_status_created_at", TryOnJobRow.status, TryOnJobRow.created_at)
Index("ix_try_on_stored_inputs_job_id_position", TryOnStoredInputRow.job_id, TryOnStoredInputRow.position)
Index("ix_try_on_status_events_job_id_position", TryOnStatusEventRow.job_id, TryOnStatusEventRow.position)
Index("ix_try_on_cost_events_job_id_position", TryOnCostEventRow.job_id, TryOnCostEventRow.position)
Index("ix_try_on_garment_slot_identity_job_position", TryOnGarmentSlotIdentityAnalysisRow.job_id, TryOnGarmentSlotIdentityAnalysisRow.position)
