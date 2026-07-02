"""Create Try-On garment slot identity analysis table."""

from alembic import op
import sqlalchemy as sa

revision = "20260623_000018"
down_revision = "20260623_000017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create per-slot garment identity analysis child table."""
    op.create_table(
        "try_on_garment_slot_identity_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("slot_role", sa.String(length=64), nullable=False),
        sa.Column("invocation_id", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty_level", sa.String(length=32), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "slot_role", name="uq_try_on_garment_slot_identity_job_role"),
    )
    op.create_index(
        "ix_try_on_garment_slot_identity_analyses_job_id",
        "try_on_garment_slot_identity_analyses",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_try_on_garment_slot_identity_analyses_invocation_id",
        "try_on_garment_slot_identity_analyses",
        ["invocation_id"],
        unique=False,
    )
    op.create_index(
        "ix_try_on_garment_slot_identity_job_position",
        "try_on_garment_slot_identity_analyses",
        ["job_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    """Drop per-slot garment identity analysis child table."""
    op.drop_index("ix_try_on_garment_slot_identity_job_position", table_name="try_on_garment_slot_identity_analyses")
    op.drop_index("ix_try_on_garment_slot_identity_analyses_invocation_id", table_name="try_on_garment_slot_identity_analyses")
    op.drop_index("ix_try_on_garment_slot_identity_analyses_job_id", table_name="try_on_garment_slot_identity_analyses")
    op.drop_table("try_on_garment_slot_identity_analyses")
