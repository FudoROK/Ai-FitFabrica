"""SQLAlchemy models for Similar Search analytics and discovery review."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class SimilarSearchClickEventRow(SqlBase):
    """Persisted product-interest event from Similar Search results."""

    __tablename__ = "similar_search_click_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    marketplace: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    offer_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    user_city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    redirect_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


Index(
    "ix_similar_search_click_events_product_created",
    SimilarSearchClickEventRow.product_id,
    SimilarSearchClickEventRow.created_at,
)


class MarketplaceDiscoveryCandidateRow(SqlBase):
    """Persisted open-web marketplace discovery candidate awaiting admin review."""

    __tablename__ = "marketplace_discovery_candidates"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "business_id",
            "source_url",
            name="uq_marketplace_discovery_candidates_scope_source_url",
        ),
    )

    candidate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    business_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    connector_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_snippet: Mapped[str | None] = mapped_column(String(512), nullable=True)
    platform_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    price_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    raw_payload_json: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(astext_type=Text()), "postgresql"),
        nullable=False,
        default=dict,
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(astext_type=Text()), "postgresql"),
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


Index(
    "ix_marketplace_discovery_candidates_status_source",
    MarketplaceDiscoveryCandidateRow.status,
    MarketplaceDiscoveryCandidateRow.source_type,
)
Index(
    "ix_marketplace_discovery_candidates_scope_status",
    MarketplaceDiscoveryCandidateRow.workspace_id,
    MarketplaceDiscoveryCandidateRow.business_id,
    MarketplaceDiscoveryCandidateRow.status,
)
