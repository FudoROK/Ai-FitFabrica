"""SQLAlchemy models for seller-owned business catalog persistence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class BusinessMerchantRow(SqlBase):
    """Persisted business merchant profile."""

    __tablename__ = "business_merchants"

    merchant_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_tier: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    tier_assigned_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    tier_assigned_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tier_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessProductRow(SqlBase):
    """Persisted seller-owned product metadata."""

    __tablename__ = "business_products"

    product_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(
        ForeignKey("business_merchants.merchant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_checked")
    category_validation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visual_category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    category_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    search_index_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_indexed")
    search_index_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessProductImageRow(SqlBase):
    """Persisted product image metadata."""

    __tablename__ = "business_product_images"

    image_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("business_products.product_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessProductOfferRow(SqlBase):
    """Persisted sellable offer for one catalog product."""

    __tablename__ = "business_product_offers"

    offer_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("business_products.product_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    availability: Mapped[str] = mapped_column(String(32), nullable=False)
    product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_regions_json: Mapped[list[str]] = mapped_column("delivery_regions", JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessCatalogImportJobRow(SqlBase):
    """Persisted catalog import job metadata."""

    __tablename__ = "business_catalog_import_jobs"

    import_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BusinessCatalogImportRowErrorRow(SqlBase):
    """Persisted row-level import validation error."""

    __tablename__ = "business_catalog_import_row_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_id: Mapped[str] = mapped_column(
        ForeignKey("business_catalog_import_jobs.import_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    safe_code: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)


Index("ix_business_products_status_review", BusinessProductRow.status, BusinessProductRow.review_status)
Index("ix_business_products_search_index_status", BusinessProductRow.search_index_status)
Index("ix_business_products_geo", BusinessProductRow.country_code, BusinessProductRow.city)
Index("ix_business_product_offers_product_url", BusinessProductOfferRow.product_url)
