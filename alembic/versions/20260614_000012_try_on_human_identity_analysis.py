"""Persist validated Try-On Human Identity analyses."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260614_000012"
down_revision = "20260614_000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the one-to-one Human Identity analysis table."""

    op.create_table(
        "try_on_human_identity_analyses",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("invocation_id", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("contract_version", sa.String(length=128), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty_level", sa.String(length=32), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(
        "ix_try_on_human_identity_analyses_invocation_id",
        "try_on_human_identity_analyses",
        ["invocation_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the Human Identity analysis table."""

    op.drop_index(
        "ix_try_on_human_identity_analyses_invocation_id",
        table_name="try_on_human_identity_analyses",
    )
    op.drop_table("try_on_human_identity_analyses")
