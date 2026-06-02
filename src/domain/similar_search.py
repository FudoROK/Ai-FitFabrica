"""Typed domain models for backend-owned similar search."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.vector_search import VectorNamespace


class SimilarSearchRequest(BaseModel):
    """Backend-owned request for similar-product retrieval."""

    model_config = ConfigDict(extra="forbid")

    source_type: Literal["text", "product_ref"]
    query_text: str | None = None
    product_id: str | None = None
    category: str | None = None
    brand: str | None = None
    budget_max: float | None = Field(default=None, ge=0)
    marketplace_filters: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, gt=0, le=50)
    reference_price: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_source_fields(self) -> "SimilarSearchRequest":
        """Require a query text for free-text requests or a product id for product-ref requests."""
        if self.source_type == "text" and not (self.query_text or "").strip():
            raise ValueError("query_text is required when source_type=text")
        if self.source_type == "product_ref" and not (self.product_id or "").strip():
            raise ValueError("product_id is required when source_type=product_ref")
        return self


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


class SimilarSearchResponse(BaseModel):
    """Structured similar-search response returned from backend APIs."""

    model_config = ConfigDict(extra="forbid")

    results: list[SimilarSearchResult] = Field(default_factory=list)
