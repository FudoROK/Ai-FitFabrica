"""Persist validated Product Card Garment Identity analyses."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260615_000014"
down_revision = "20260615_000013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the one-to-one Product Card garment-analysis table."""
    op.create_table(
        "product_card_garment_analyses",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("invocation_id", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("contract_version", sa.String(length=128), nullable=False),
        sa.Column("garment_type", sa.String(length=128), nullable=False),
        sa.Column("dominant_color", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty_level", sa.String(length=32), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["product_card_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(
        "ix_product_card_garment_analyses_invocation_id",
        "product_card_garment_analyses",
        ["invocation_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the Product Card garment-analysis table."""
    op.drop_index("ix_product_card_garment_analyses_invocation_id", table_name="product_card_garment_analyses")
    op.drop_table("product_card_garment_analyses")
