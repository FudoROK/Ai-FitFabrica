from __future__ import annotations

import pytest

from src.adapters.similar_search.search_engine_discovery import (
    DisabledSearchEngineDiscoveryConnector,
    SearchEngineResult,
    build_instagram_public_discovery_query,
    build_search_engine_discovery_connector,
    map_search_results_to_discovery_candidates,
)
from src.domain.marketplace_search import (
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
    MarketplaceLegalAccessType,
    MarketplaceSourceType,
)


def test_instagram_public_discovery_query_is_site_scoped_and_location_aware() -> None:
    query_text = build_instagram_public_discovery_query(
        normalized_terms=["white shirt", "button up"],
        user_city="Almaty",
        user_country_code="KZ",
    )

    assert "site:instagram.com" in query_text
    assert "white shirt" in query_text
    assert "button up" in query_text
    assert "Almaty" in query_text
    assert "KZ" in query_text


def test_search_engine_results_map_instagram_links_to_candidates_only() -> None:
    candidates = map_search_results_to_discovery_candidates(
        connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        category="shirt",
        user_country_code="KZ",
        user_city="Almaty",
        results=[
            SearchEngineResult(
                provider="test_search",
                rank=1,
                title="Example shop white shirt",
                url="https://www.instagram.com/example_shop/p/example",
                snippet="White shirt in Almaty.",
            ),
            SearchEngineResult(
                provider="test_search",
                rank=2,
                title="Unrelated page",
                url="https://example.test/not-instagram",
                snippet="Not an Instagram result.",
            ),
        ],
    )

    assert len(candidates) == 1
    assert candidates[0].candidate_id == "test_search:1"
    assert str(candidates[0].source_url) == "https://www.instagram.com/example_shop/p/example"
    assert candidates[0].platform_hint == "instagram"
    assert candidates[0].requires_review is True


def test_search_engine_result_mapper_rejects_lookalike_instagram_domains() -> None:
    candidates = map_search_results_to_discovery_candidates(
        connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        category="shirt",
        user_country_code="KZ",
        user_city="Almaty",
        results=[
            SearchEngineResult(
                provider="test_search",
                rank=1,
                title="Lookalike result",
                url="https://instagram.com.evil.example/product",
                snippet="Looks like Instagram but is not.",
            )
        ],
    )

    assert candidates == []


@pytest.mark.asyncio
async def test_disabled_search_engine_discovery_connector_returns_skipped_without_network() -> None:
    connector = DisabledSearchEngineDiscoveryConnector()
    report = await connector.search(
        query=MarketplaceConnectorQuery(
            connector_kind=MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY,
            source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
            legal_access_type=MarketplaceLegalAccessType.SEARCH_ENGINE_API,
            user_country_code="KZ",
            user_city="Almaty",
            category="shirt",
            normalized_terms=["white shirt"],
        )
    )

    assert report.connector_kind is MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY
    assert report.status is MarketplaceConnectorStatus.SKIPPED
    assert report.candidates == []
    assert report.error_code == "search_engine_not_configured"


@pytest.mark.asyncio
async def test_search_engine_connector_factory_returns_disabled_when_feature_is_off() -> None:
    connector = build_search_engine_discovery_connector(
        enabled=False,
        provider="google_programmable_search",
        api_key="secret",
    )

    report = await connector.search(
        query=MarketplaceConnectorQuery(
            connector_kind=MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY,
            source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
            legal_access_type=MarketplaceLegalAccessType.SEARCH_ENGINE_API,
            user_country_code="KZ",
            user_city="Almaty",
            category="shirt",
            normalized_terms=["white shirt"],
        )
    )

    assert report.status is MarketplaceConnectorStatus.SKIPPED
    assert report.error_code == "search_engine_not_configured"


@pytest.mark.asyncio
async def test_search_engine_connector_factory_returns_safe_skipped_for_unknown_provider() -> None:
    connector = build_search_engine_discovery_connector(
        enabled=True,
        provider="unknown_provider",
        api_key="secret",
    )

    report = await connector.search(
        query=MarketplaceConnectorQuery(
            connector_kind=MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY,
            source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
            legal_access_type=MarketplaceLegalAccessType.SEARCH_ENGINE_API,
            user_country_code="KZ",
            user_city="Almaty",
            category="shirt",
            normalized_terms=["white shirt"],
        )
    )

    assert report.status is MarketplaceConnectorStatus.SKIPPED
    assert report.error_code == "search_engine_provider_not_supported"
