"""Add business product catalog tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260628_000021"
down_revision = "20260624_000020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create seller-owned business catalog tables."""

    op.create_table(
        "business_merchants",
        sa.Column("merchant_id", sa.String(length=128), primary_key=True),
        sa.Column("owner_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("instagram_url", sa.Text(), nullable=True),
        sa.Column("website_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_tier", sa.String(length=32), nullable=False, server_default="standard"),
        sa.Column("tier_assigned_reason", sa.Text(), nullable=True),
        sa.Column("tier_assigned_by", sa.String(length=128), nullable=True),
        sa.Column("tier_assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_business_merchants_owner_id", "business_merchants", ["owner_id"])

    op.create_table(
        "business_products",
        sa.Column("product_id", sa.String(length=128), primary_key=True),
        sa.Column("merchant_id", sa.String(length=128), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["business_merchants.merchant_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_business_products_merchant_id", "business_products", ["merchant_id"])
    op.create_index("ix_business_products_owner_id", "business_products", ["owner_id"])
    op.create_index("ix_business_products_status_review", "business_products", ["status", "review_status"])
    op.create_index("ix_business_products_geo", "business_products", ["country_code", "city"])

    op.create_table(
        "business_product_images",
        sa.Column("image_id", sa.String(length=128), primary_key=True),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["business_products.product_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_business_product_images_product_id", "business_product_images", ["product_id"])

    op.create_table(
        "business_product_offers",
        sa.Column("offer_id", sa.String(length=128), primary_key=True),
        sa.Column("product_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("availability", sa.String(length=32), nullable=False),
        sa.Column("product_url", sa.Text(), nullable=True),
        sa.Column("delivery_regions", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["business_products.product_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_business_product_offers_product_id", "business_product_offers", ["product_id"])
    op.create_index("ix_business_product_offers_product_url", "business_product_offers", ["product_url"])

    op.create_table(
        "business_catalog_import_jobs",
        sa.Column("import_id", sa.String(length=128), primary_key=True),
        sa.Column("merchant_id", sa.String(length=128), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("accepted_rows", sa.Integer(), nullable=False),
        sa.Column("rejected_rows", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_business_catalog_import_jobs_merchant_id", "business_catalog_import_jobs", ["merchant_id"])
    op.create_index("ix_business_catalog_import_jobs_owner_id", "business_catalog_import_jobs", ["owner_id"])

    op.create_table(
        "business_catalog_import_row_errors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("import_id", sa.String(length=128), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=128), nullable=False),
        sa.Column("safe_code", sa.String(length=128), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["business_catalog_import_jobs.import_id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_business_catalog_import_row_errors_import_id",
        "business_catalog_import_row_errors",
        ["import_id"],
    )


def downgrade() -> None:
    """Drop seller-owned business catalog tables."""

    op.drop_index("ix_business_catalog_import_row_errors_import_id", table_name="business_catalog_import_row_errors")
    op.drop_table("business_catalog_import_row_errors")
    op.drop_index("ix_business_catalog_import_jobs_owner_id", table_name="business_catalog_import_jobs")
    op.drop_index("ix_business_catalog_import_jobs_merchant_id", table_name="business_catalog_import_jobs")
    op.drop_table("business_catalog_import_jobs")
    op.drop_index("ix_business_product_offers_product_url", table_name="business_product_offers")
    op.drop_index("ix_business_product_offers_product_id", table_name="business_product_offers")
    op.drop_table("business_product_offers")
    op.drop_index("ix_business_product_images_product_id", table_name="business_product_images")
    op.drop_table("business_product_images")
    op.drop_index("ix_business_products_geo", table_name="business_products")
    op.drop_index("ix_business_products_status_review", table_name="business_products")
    op.drop_index("ix_business_products_owner_id", table_name="business_products")
    op.drop_index("ix_business_products_merchant_id", table_name="business_products")
    op.drop_table("business_products")
    op.drop_index("ix_business_merchants_owner_id", table_name="business_merchants")
    op.drop_table("business_merchants")
