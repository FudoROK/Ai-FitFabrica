from __future__ import annotations

import pytest

from src.adapters.similar_search.marketplace_connectors import (
    DisabledMarketplaceConnector,
    MarketplaceConnectorRegistry,
    build_default_marketplace_connector_registry,
    build_marketplace_connector_registry,
)
from src.domain.marketplace_search import (
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
    MarketplaceLegalAccessType,
    MarketplaceSourceType,
)


def _query(kind: MarketplaceConnectorKind) -> MarketplaceConnectorQuery:
    return MarketplaceConnectorQuery(
        connector_kind=kind,
        source_type=MarketplaceSourceType.OFFICIAL_API,
        legal_access_type=MarketplaceLegalAccessType.OFFICIAL_API,
        user_country_code="KZ",
        user_city="Almaty",
        category="shirt",
        normalized_terms=["white shirt"],
    )


def test_default_marketplace_connector_registry_registers_disabled_future_connectors() -> None:
    registry = build_default_marketplace_connector_registry()

    assert registry.get(MarketplaceConnectorKind.KASPI) is not None
    assert registry.get(MarketplaceConnectorKind.WILDBERRIES) is not None
    assert registry.get(MarketplaceConnectorKind.INSTAGRAM_BUSINESS) is not None
    assert registry.get(MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY) is not None
    assert registry.get(MarketplaceConnectorKind.PUBLIC_WEB_ALLOWED) is not None
    assert registry.get(MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY) is not None


@pytest.mark.asyncio
async def test_disabled_marketplace_connector_returns_skipped_report_without_network_call() -> None:
    connector = DisabledMarketplaceConnector(
        connector_kind=MarketplaceConnectorKind.KASPI,
        reason="Official API credentials are not configured.",
    )

    report = await connector.search(query=_query(MarketplaceConnectorKind.KASPI))

    assert report.connector_kind is MarketplaceConnectorKind.KASPI
    assert report.status is MarketplaceConnectorStatus.SKIPPED
    assert report.offers == []
    assert report.error_code == "connector_not_configured"


def test_marketplace_connector_registry_rejects_duplicate_connector_kind() -> None:
    registry = MarketplaceConnectorRegistry()
    connector = DisabledMarketplaceConnector(
        connector_kind=MarketplaceConnectorKind.KASPI,
        reason="Official API credentials are not configured.",
    )

    registry.register(connector)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(connector)


@pytest.mark.asyncio
async def test_marketplace_connector_registry_factory_uses_safe_search_engine_settings() -> None:
    registry = build_marketplace_connector_registry(
        search_engine_discovery_enabled=True,
        search_engine_discovery_provider="unknown_provider",
        search_engine_discovery_api_key="secret",
    )

    connector = registry.get(MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY)
    assert connector is not None

    report = await connector.search(query=_query(MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY))

    assert report.status is MarketplaceConnectorStatus.SKIPPED
    assert report.error_code == "search_engine_provider_not_supported"
