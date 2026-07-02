"""Persist the product category on product-card jobs."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260615_000013"
down_revision = "20260614_000012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add a required category while preserving existing product-card jobs."""
    op.add_column(
        "product_card_jobs",
        sa.Column("category", sa.String(length=128), nullable=False, server_default="uncategorized"),
    )
    op.alter_column("product_card_jobs", "category", server_default=None)


def downgrade() -> None:
    """Remove the persisted product-card category."""
    op.drop_column("product_card_jobs", "category")
