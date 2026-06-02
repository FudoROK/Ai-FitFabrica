"""Reliability and operations foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000009"
down_revision = "20260531_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create durable queue job and worker lease tables."""
    op.create_table(
        "workflow_queue_jobs",
        sa.Column("queue_job_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_type", sa.String(length=64), nullable=False),
        sa.Column("workflow_reference", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("queue_job_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_table(
        "worker_leases",
        sa.Column("lease_id", sa.String(length=64), nullable=False),
        sa.Column("queue_job_id", sa.String(length=64), nullable=False),
        sa.Column("worker_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["queue_job_id"], ["workflow_queue_jobs.queue_job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("lease_id"),
    )
    op.create_index(
        "ix_workflow_queue_jobs_status_created_at",
        "workflow_queue_jobs",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop durable queue job and worker lease tables."""
    op.drop_index("ix_workflow_queue_jobs_status_created_at", table_name="workflow_queue_jobs")
    op.drop_table("worker_leases")
    op.drop_table("workflow_queue_jobs")
