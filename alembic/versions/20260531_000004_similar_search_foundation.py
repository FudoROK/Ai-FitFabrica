"""Similar search foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000004"
down_revision = "20260531_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create product catalog and marketplace-offer tables for similar search."""
    op.create_table(
        "products",
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("brand", sa.String(length=64), nullable=False),
        sa.Column("color", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("product_id"),
    )
    op.create_table(
        "marketplace_offers",
        sa.Column("offer_id", sa.String(length=64), nullable=False),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("marketplace", sa.String(length=64), nullable=False),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("product_url", sa.String(length=1024), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("offer_id"),
    )
    op.create_table(
        "price_snapshots",
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("offer_id", sa.String(length=64), nullable=False),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["offer_id"], ["marketplace_offers.offer_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_index("ix_products_category_brand", "products", ["category", "brand"], unique=False)
    op.create_index("ix_marketplace_offers_product_marketplace", "marketplace_offers", ["product_id", "marketplace"], unique=False)


def downgrade() -> None:
    """Drop similar-search catalog tables."""
    op.drop_index("ix_marketplace_offers_product_marketplace", table_name="marketplace_offers")
    op.drop_index("ix_products_category_brand", table_name="products")
    op.drop_table("price_snapshots")
    op.drop_table("marketplace_offers")
    op.drop_table("products")
