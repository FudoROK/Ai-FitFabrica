"""Try-On rebase foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000003"
down_revision = "20260531_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create portable SQL tables for Try-On jobs and child records."""
    op.create_table(
        "try_on_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_type", sa.String(length=32), nullable=False),
        sa.Column("generation_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_table(
        "try_on_stored_inputs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("storage_backend", sa.String(length=32), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("bucket_name", sa.String(length=255), nullable=True),
        sa.Column("object_key", sa.Text(), nullable=True),
        sa.Column("object_name", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "position", name="uq_try_on_stored_inputs_job_position"),
    )
    op.create_table(
        "try_on_status_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "position", name="uq_try_on_status_events_job_position"),
    )
    op.create_table(
        "try_on_cost_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("estimated_units", sa.Integer(), nullable=False),
        sa.Column("charge_status", sa.String(length=32), nullable=False),
        sa.Column("charged_credits", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "position", name="uq_try_on_cost_events_job_position"),
    )
    op.create_table(
        "try_on_results",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("result_image", sa.JSON(), nullable=False),
        sa.Column("quality_report", sa.JSON(), nullable=False),
        sa.Column("stylist_note", sa.Text(), nullable=False),
        sa.Column("input_metadata", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_table(
        "try_on_errors",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_try_on_jobs_status_created_at", "try_on_jobs", ["status", "created_at"], unique=False)
    op.create_index("ix_try_on_stored_inputs_job_id_position", "try_on_stored_inputs", ["job_id", "position"], unique=False)
    op.create_index("ix_try_on_status_events_job_id_position", "try_on_status_events", ["job_id", "position"], unique=False)
    op.create_index("ix_try_on_cost_events_job_id_position", "try_on_cost_events", ["job_id", "position"], unique=False)


def downgrade() -> None:
    """Drop portable SQL tables for Try-On jobs and child records."""
    op.drop_index("ix_try_on_cost_events_job_id_position", table_name="try_on_cost_events")
    op.drop_index("ix_try_on_status_events_job_id_position", table_name="try_on_status_events")
    op.drop_index("ix_try_on_stored_inputs_job_id_position", table_name="try_on_stored_inputs")
    op.drop_index("ix_try_on_jobs_status_created_at", table_name="try_on_jobs")
    op.drop_table("try_on_errors")
    op.drop_table("try_on_results")
    op.drop_table("try_on_cost_events")
    op.drop_table("try_on_status_events")
    op.drop_table("try_on_stored_inputs")
    op.drop_table("try_on_jobs")
