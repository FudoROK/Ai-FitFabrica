"""Persist Try-On Garment Identity and Material / Texture analyses."""

from alembic import op
import sqlalchemy as sa

revision = "20260615_000015"
down_revision = "20260615_000014"
branch_labels = None
depends_on = None


def _create_analysis_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("invocation_id", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty_level", sa.String(length=32), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["try_on_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(f"ix_{name}_invocation_id", name, ["invocation_id"], unique=False)


def upgrade() -> None:
    """Create one-to-one Try-On analysis child tables."""
    _create_analysis_table("try_on_garment_identity_analyses")
    _create_analysis_table("try_on_material_texture_analyses")


def downgrade() -> None:
    """Drop Try-On analysis child tables."""
    for name in ("try_on_material_texture_analyses", "try_on_garment_identity_analyses"):
        op.drop_index(f"ix_{name}_invocation_id", table_name=name)
        op.drop_table(name)
