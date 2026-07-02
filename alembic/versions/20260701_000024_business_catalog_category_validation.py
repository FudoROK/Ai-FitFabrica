"""Add business catalog category validation state."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260701_000024"
down_revision = "20260701_000023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Persist visual category validation before product approval."""

    op.add_column(
        "business_products",
        sa.Column("category_validation_status", sa.String(length=32), nullable=False, server_default="not_checked"),
    )
    op.add_column("business_products", sa.Column("category_validation_reason", sa.Text(), nullable=True))
    op.add_column("business_products", sa.Column("visual_category", sa.String(length=128), nullable=True))
    op.add_column("business_products", sa.Column("visual_category_confidence", sa.Float(), nullable=True))
    op.add_column("business_products", sa.Column("category_validated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_business_products_category_validation_status",
        "business_products",
        ["category_validation_status"],
    )


def downgrade() -> None:
    """Remove business catalog category validation state."""

    op.drop_index("ix_business_products_category_validation_status", table_name="business_products")
    op.drop_column("business_products", "category_validated_at")
    op.drop_column("business_products", "visual_category_confidence")
    op.drop_column("business_products", "visual_category")
    op.drop_column("business_products", "category_validation_reason")
    op.drop_column("business_products", "category_validation_status")
