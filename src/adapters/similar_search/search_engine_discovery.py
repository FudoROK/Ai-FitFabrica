"""Search-engine discovery adapter primitives for open web candidates."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.domain.marketplace_search import (
    MarketplaceConnectorExecutionReport,
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
    MarketplaceDiscoveryCandidate,
    MarketplaceSourceType,
)


class SearchEngineResult(BaseModel):
    """One normalized result returned by a future official search-engine API adapter."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=64)
    rank: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    snippet: str | None = Field(default=None, min_length=1, max_length=512)


def build_instagram_public_discovery_query(
    *,
    normalized_terms: list[str],
    user_city: str,
    user_country_code: str,
) -> str:
    """Build a site-scoped search query for Instagram public discovery candidates."""

    terms = " ".join(term.strip() for term in normalized_terms if term.strip())
    location = f"{user_city.strip()} {user_country_code.strip().upper()}".strip()
    return f"site:instagram.com {terms} {location}".strip()


def map_search_results_to_discovery_candidates(
    *,
    connector_kind: MarketplaceConnectorKind,
    source_type: MarketplaceSourceType,
    category: str,
    user_country_code: str,
    user_city: str,
    results: list[SearchEngineResult],
) -> list[MarketplaceDiscoveryCandidate]:
    """Map allowed search-engine results into review-required discovery candidates."""

    candidates: list[MarketplaceDiscoveryCandidate] = []
    for result in results:
        if not _is_allowed_instagram_url(str(result.url)):
            continue
        candidates.append(
            MarketplaceDiscoveryCandidate(
                candidate_id=f"{result.provider}:{result.rank}",
                connector_kind=connector_kind,
                source_type=source_type,
                source_url=result.url,
                source_title=result.title,
                source_snippet=result.snippet,
                platform_hint="instagram",
                category=category,
                country_code=user_country_code,
                city=user_city,
            )
        )
    return candidates


def _is_allowed_instagram_url(url: str) -> bool:
    """Return whether a URL is a public Instagram URL candidate."""

    hostname = (urlparse(url).hostname or "").casefold()
    return hostname == "instagram.com" or hostname.endswith(".instagram.com")


class DisabledSearchEngineDiscoveryConnector:
    """Safe placeholder until an official search-engine API is configured."""

    connector_kind = MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        """Return skipped without network calls, scraping, or browser automation."""

        return MarketplaceConnectorExecutionReport(
            connector_kind=self.connector_kind,
            status=MarketplaceConnectorStatus.SKIPPED,
            offers=[],
            candidates=[],
            error_code="search_engine_not_configured",
            error_message=(
                "Search engine discovery requires an official search API key and usage policy before live calls."
            ),
        )


class UnsupportedSearchEngineDiscoveryConnector:
    """Safe placeholder when settings request a provider that is not implemented."""

    connector_kind = MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY

    def __init__(self, *, provider: str) -> None:
        """Store the unsupported provider name for diagnostics."""

        self._provider = provider

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        """Return skipped so enabling an unknown provider cannot trigger live calls."""

        return MarketplaceConnectorExecutionReport(
            connector_kind=self.connector_kind,
            status=MarketplaceConnectorStatus.SKIPPED,
            offers=[],
            candidates=[],
            error_code="search_engine_provider_not_supported",
            error_message=f"Search engine discovery provider is not supported: {self._provider}",
        )


def build_search_engine_discovery_connector(
    *,
    enabled: bool,
    provider: str,
    api_key: str | None,
) -> DisabledSearchEngineDiscoveryConnector | UnsupportedSearchEngineDiscoveryConnector:
    """Build the safe search-engine discovery connector for current settings."""

    normalized_provider = provider.strip().casefold()
    if not enabled or not api_key or normalized_provider in {"", "disabled"}:
        return DisabledSearchEngineDiscoveryConnector()
    return UnsupportedSearchEngineDiscoveryConnector(provider=provider)
