"""Typed domain models for backend-owned similar search."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.vector_search import VectorNamespace


class SimilarSearchRequest(BaseModel):
    """Backend-owned request for similar-product retrieval."""

    model_config = ConfigDict(extra="forbid")

    source_type: Literal["text", "product_ref", "garment_photo"]
    query_text: str | None = None
    product_id: str | None = None
    garment_profile: "SimilarSearchGarmentProfile | None" = None
    category: str | None = None
    brand: str | None = None
    budget_max: float | None = Field(default=None, ge=0)
    marketplace_filters: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, gt=0, le=50)
    reference_price: float | None = Field(default=None, ge=0)
    user_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    user_city: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def _validate_source_fields(self) -> "SimilarSearchRequest":
        """Require a query text for free-text requests or a product id for product-ref requests."""
        if self.source_type == "text" and not (self.query_text or "").strip():
            raise ValueError("query_text is required when source_type=text")
        if self.source_type == "product_ref" and not (self.product_id or "").strip():
            raise ValueError("product_id is required when source_type=product_ref")
        if self.source_type == "garment_photo" and self.garment_profile is None:
            raise ValueError("garment_profile is required when source_type=garment_photo")
        return self


class SimilarSearchGarmentProfile(BaseModel):
    """Backend-approved garment facts used to search similar catalog products."""

    model_config = ConfigDict(extra="forbid")

    garment_type: str = Field(min_length=1)
    dominant_color: str = Field(min_length=1)
    secondary_colors: list[str] = Field(default_factory=list)
    silhouette_summary: str = Field(min_length=1)
    preserved_details: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class CatalogProductRecord(BaseModel):
    """Canonical product truth used to hydrate retrieval hits."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    brand: str = Field(min_length=1)
    color: str | None = None


class CatalogOfferRecord(BaseModel):
    """Marketplace offer metadata attached to a product."""

    model_config = ConfigDict(extra="forbid")

    offer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    marketplace: str = Field(min_length=1)
    price_amount: float = Field(ge=0)
    currency: str = Field(min_length=1)
    product_url: str = Field(min_length=1)
    is_available: bool = True
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = Field(default=None, min_length=1, max_length=128)
    delivery_regions: list[str] = Field(default_factory=list)
    source_trust_score: float = Field(default=0.5, ge=0, le=1)


class SimilarityQueryProfile(BaseModel):
    """Prepared backend-owned query profile before embedding and retrieval."""

    model_config = ConfigDict(extra="forbid")

    embedding_input: str = Field(min_length=1)
    vector_namespace: VectorNamespace = VectorNamespace.PRODUCTS
    budget_max: float | None = Field(default=None, ge=0)
    marketplace_filters: list[str] = Field(default_factory=list)
    category: str | None = None
    brand: str | None = None
    reference_price: float | None = Field(default=None, ge=0)


class HydratedCatalogMatch(BaseModel):
    """One retrieved match enriched with catalog truth and offer metadata."""

    model_config = ConfigDict(extra="forbid")

    product: CatalogProductRecord
    offer: CatalogOfferRecord
    similarity_score: float


class SimilarSearchResult(BaseModel):
    """One ranked result returned to the client."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    similarity_score: float
    price_amount: float = Field(ge=0)
    currency: str = Field(min_length=1)
    marketplace: str = Field(min_length=1)
    is_cheaper_alternative: bool
    explanation: str = Field(min_length=1)
    location_match: str = Field(default="unknown", min_length=1)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = Field(default=None, min_length=1, max_length=128)
    delivery_regions: list[str] = Field(default_factory=list)
    image_url: str | None = Field(default=None, min_length=1)
    offer_url: str | None = Field(default=None, min_length=1)


class SimilarSearchResponse(BaseModel):
    """Structured similar-search response returned from backend APIs."""

    model_config = ConfigDict(extra="forbid")

    results: list[SimilarSearchResult] = Field(default_factory=list)


class SimilarSearchClickEventRequest(BaseModel):
    """Client-visible request to record interest in one similar-search result."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    marketplace: str = Field(min_length=1, max_length=128)
    offer_url: str = Field(min_length=1, max_length=2048)
    image_url: str | None = Field(default=None, min_length=1, max_length=2048)
    user_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    user_city: str | None = Field(default=None, min_length=1, max_length=128)
    source: Literal["workspace_similar_search"] = "workspace_similar_search"


class SimilarSearchClickEvent(BaseModel):
    """Persisted analytics event for a user opening a similar-search product."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    product_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    marketplace: str = Field(min_length=1, max_length=128)
    offer_url: str = Field(min_length=1, max_length=2048)
    image_url: str | None = Field(default=None, min_length=1, max_length=2048)
    user_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    user_city: str | None = Field(default=None, min_length=1, max_length=128)
    source: Literal["workspace_similar_search"] = "workspace_similar_search"
    redirect_allowed: bool
    created_at: datetime


class SimilarSearchClickEventResponse(BaseModel):
    """Response returned after a product interest event is recorded."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    redirect_url: str | None = Field(default=None, min_length=1, max_length=2048)
    redirect_allowed: bool


class SimilarSearchClickAnalyticsItem(BaseModel):
    """One aggregate row for Similar Search click analytics."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    click_count: int = Field(ge=0)


class SimilarSearchClickAnalyticsSummary(BaseModel):
    """High-level Similar Search click counters."""

    model_config = ConfigDict(extra="forbid")

    total_clicks: int = Field(ge=0)
    redirect_clicks: int = Field(ge=0)
    local_only_clicks: int = Field(ge=0)


class SimilarSearchClickAnalyticsResponse(BaseModel):
    """Admin-facing read-only analytics for free Similar Search."""

    model_config = ConfigDict(extra="forbid")

    summary: SimilarSearchClickAnalyticsSummary
    top_products: list[SimilarSearchClickAnalyticsItem] = Field(default_factory=list)
    top_marketplaces: list[SimilarSearchClickAnalyticsItem] = Field(default_factory=list)
    top_cities: list[SimilarSearchClickAnalyticsItem] = Field(default_factory=list)
