"""Provider-safe contracts for marketplace and catalog search sources."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StrictMarketplaceSearchModel(BaseModel):
    """Base model for strict marketplace search contracts."""

    model_config = ConfigDict(extra="forbid")


class MarketplaceSourceType(StrEnum):
    """Approved data-source types for marketplace/search connectors."""

    INSTAGRAM = "instagram"
    OPEN_WEB = "open_web"
    MANUAL = "manual"
    OTHER = "other"
    LOCAL_CATALOG = "local_catalog"
    PARTNER_FEED = "partner_feed"
    OFFICIAL_API = "official_api"
    SELLER_CONNECTED_STORE = "seller_connected_store"
    ADMIN_VERIFIED_LINK = "admin_verified_link"
    INSTAGRAM_BUSINESS = "instagram_business"
    PUBLIC_WEB_ALLOWED = "public_web_allowed"
    SEARCH_ENGINE_DISCOVERY = "search_engine_discovery"
    INSTAGRAM_PUBLIC_DISCOVERY = "instagram_public_discovery"


class MarketplaceConnectorKind(StrEnum):
    """Named connector families that backend may execute through approved adapters."""

    LOCAL_CATALOG = "local_catalog"
    KASPI = "kaspi"
    WILDBERRIES = "wildberries"
    INSTAGRAM_BUSINESS = "instagram_business"
    PARTNER_FEED = "partner_feed"
    SELLER_CONNECTED_STORE = "seller_connected_store"
    PUBLIC_WEB_ALLOWED = "public_web_allowed"
    SEARCH_ENGINE_DISCOVERY = "search_engine_discovery"
    INSTAGRAM_PUBLIC_DISCOVERY = "instagram_public_discovery"


class MarketplaceLegalAccessType(StrEnum):
    """Legal access basis for a connector run."""

    INTERNAL_CATALOG = "internal_catalog"
    OFFICIAL_API = "official_api"
    PARTNER_FEED = "partner_feed"
    SELLER_OAUTH = "seller_oauth"
    ADMIN_VERIFIED_LINK = "admin_verified_link"
    INSTAGRAM_GRAPH_API = "instagram_graph_api"
    PUBLIC_WEB_ALLOWED = "public_web_allowed"
    SEARCH_ENGINE_API = "search_engine_api"


class MarketplaceConnectorStatus(StrEnum):
    """Per-connector execution status isolated from the whole search workflow."""

    SUCCEEDED = "succeeded"
    NO_RESULTS = "no_results"
    FAILED = "failed"
    SKIPPED = "skipped"


class MarketplaceDiscoveryCandidateStatus(StrEnum):
    """Review status for open web/search discovery candidates."""

    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class MarketplaceConnectorQuery(StrictMarketplaceSearchModel):
    """Backend-owned query sent to one approved marketplace/search adapter."""

    connector_kind: MarketplaceConnectorKind
    source_type: MarketplaceSourceType
    legal_access_type: MarketplaceLegalAccessType
    user_country_code: str = Field(min_length=2, max_length=2)
    user_city: str = Field(min_length=1, max_length=128)
    category: str = Field(min_length=1, max_length=128)
    normalized_terms: list[str] = Field(min_length=1)
    budget_max: float | None = Field(default=None, ge=0)
    limit: int = Field(default=20, gt=0, le=50)


class NormalizedMarketplaceOffer(StrictMarketplaceSearchModel):
    """One normalized connector result after backend validation."""

    source_type: MarketplaceSourceType
    source_id: str = Field(min_length=1, max_length=128)
    product_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    price_amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    delivery_regions: list[str] = Field(default_factory=list)
    product_url: HttpUrl
    is_available: bool = True
    source_trust_score: float = Field(ge=0, le=1)


class MarketplaceDiscoveryCandidate(StrictMarketplaceSearchModel):
    """Non-sellable candidate discovered from public web/search sources."""

    candidate_id: str = Field(min_length=1, max_length=128)
    workspace_id: str | None = Field(default=None, min_length=1, max_length=128)
    business_id: str | None = Field(default=None, min_length=1, max_length=128)
    connector_kind: MarketplaceConnectorKind
    source_type: MarketplaceSourceType
    source_url: HttpUrl
    image_url: HttpUrl | None = None
    media_url: HttpUrl | None = None
    source_title: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    brand: str | None = Field(default=None, min_length=1, max_length=128)
    source_snippet: str | None = Field(default=None, min_length=1, max_length=512)
    platform_hint: str | None = Field(default=None, min_length=1, max_length=64)
    category: str | None = Field(default=None, min_length=1, max_length=128)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = Field(default=None, min_length=1, max_length=128)
    price_amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    raw_payload: dict[str, object] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)
    status: MarketplaceDiscoveryCandidateStatus = MarketplaceDiscoveryCandidateStatus.PENDING
    rejection_reason: str | None = Field(default=None, min_length=1, max_length=512)
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def requires_review(self) -> bool:
        """Return whether this candidate still needs validation before catalog use."""

        return self.status in {
            MarketplaceDiscoveryCandidateStatus.PENDING,
            MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW,
        }


class MarketplaceConnectorExecutionReport(StrictMarketplaceSearchModel):
    """Result of one connector run with failure isolated from other sources."""

    connector_kind: MarketplaceConnectorKind
    status: MarketplaceConnectorStatus
    offers: list[NormalizedMarketplaceOffer] = Field(default_factory=list)
    candidates: list[MarketplaceDiscoveryCandidate] = Field(default_factory=list)
    error_code: str | None = Field(default=None, min_length=1, max_length=128)
    error_message: str | None = Field(default=None, min_length=1, max_length=512)

    @property
    def is_successful(self) -> bool:
        """Return whether this connector result can be safely merged into search output."""

        return self.status in {MarketplaceConnectorStatus.SUCCEEDED, MarketplaceConnectorStatus.NO_RESULTS}


class MarketplaceSearchSourcePolicy:
    """Central allow/deny policy for marketplace search data sources."""

    _disallowed_source_names = frozenset(
        {
            "hidden_scraping",
            "hidden_scraper",
            "browser_automation",
            "marketplace_scraping",
            "unapproved_scraping",
        }
    )

    def is_allowed(self, source_type: MarketplaceSourceType) -> Literal[True]:
        """Return True for all enum-backed approved source types."""

        return True

    def is_disallowed_source_name(self, source_name: str) -> bool:
        """Return whether a free-form source name is explicitly disallowed."""

        return source_name.strip().lower() in self._disallowed_source_names
