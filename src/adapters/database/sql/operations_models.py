"""Portable SQLAlchemy models for queue jobs and worker leases."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class QueueJobRow(SqlBase):
    """Durable queue job row for backend-owned workflow dispatch."""

    __tablename__ = "workflow_queue_jobs"

    queue_job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(64), nullable=False)
    workflow_reference: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    last_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkerLeaseRow(SqlBase):
    """Durable worker lease row bound to one queue job."""

    __tablename__ = "worker_leases"

    lease_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    queue_job_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_queue_jobs.queue_job_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


Index("ix_workflow_queue_jobs_status_created_at", QueueJobRow.status, QueueJobRow.created_at)
