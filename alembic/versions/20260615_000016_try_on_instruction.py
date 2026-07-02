"""Persist validated Try-On generation instructions."""

from alembic import op
import sqlalchemy as sa

revision = "20260615_000016"
down_revision = "20260615_000015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the one-to-one Try-On instruction child table."""
    op.create_table(
        "try_on_instructions",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("invocation_id", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty_level", sa.String(length=32), nullable=False),
        sa.Column("instruction", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_try_on_instructions_invocation_id", "try_on_instructions", ["invocation_id"], unique=False)


def downgrade() -> None:
    """Drop the Try-On instruction child table."""
    op.drop_index("ix_try_on_instructions_invocation_id", table_name="try_on_instructions")
    op.drop_table("try_on_instructions")
