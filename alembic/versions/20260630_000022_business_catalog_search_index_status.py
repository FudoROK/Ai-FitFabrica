"""Add business catalog search index status fields."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260630_000022"
down_revision = "20260628_000021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Track whether approved catalog products are indexed for search."""

    op.add_column(
        "business_products",
        sa.Column("search_index_status", sa.String(length=32), nullable=False, server_default="not_indexed"),
    )
    op.add_column("business_products", sa.Column("search_index_error", sa.Text(), nullable=True))
    op.add_column("business_products", sa.Column("search_indexed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_business_products_search_index_status",
        "business_products",
        ["search_index_status"],
    )
    op.alter_column("business_products", "search_index_status", server_default=None)


def downgrade() -> None:
    """Remove search indexing state from business products."""

    op.drop_index("ix_business_products_search_index_status", table_name="business_products")
    op.drop_column("business_products", "search_indexed_at")
    op.drop_column("business_products", "search_index_error")
    op.drop_column("business_products", "search_index_status")
