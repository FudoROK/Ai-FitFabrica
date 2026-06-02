"""Portable SQLAlchemy models for product-catalog hydration."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class ProductRow(SqlBase):
    """Canonical product metadata used for similar-search hydration."""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    brand: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketplaceOfferRow(SqlBase):
    """Marketplace offer bound to one canonical product."""

    __tablename__ = "marketplace_offers"

    offer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(64), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    product_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PriceSnapshotRow(SqlBase):
    """Historical price snapshot for future marketplace intelligence use."""

    __tablename__ = "price_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    offer_id: Mapped[str] = mapped_column(ForeignKey("marketplace_offers.offer_id", ondelete="CASCADE"), nullable=False, index=True)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_products_category_brand", ProductRow.category, ProductRow.brand)
Index("ix_marketplace_offers_product_marketplace", MarketplaceOfferRow.product_id, MarketplaceOfferRow.marketplace)
