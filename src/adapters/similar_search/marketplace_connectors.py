"""Marketplace connector registry and disabled future connector adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.marketplace_search import (
    MarketplaceConnectorExecutionReport,
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
)
from src.adapters.similar_search.search_engine_discovery import build_search_engine_discovery_connector


class MarketplaceConnectorAdapter(Protocol):
    """Adapter shape required by the marketplace connector registry."""

    connector_kind: MarketplaceConnectorKind

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        """Return one isolated connector execution report."""


@dataclass(frozen=True)
class DisabledMarketplaceConnector:
    """Safe placeholder for a connector that is not legally/configuration-ready."""

    connector_kind: MarketplaceConnectorKind
    reason: str

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        """Return a skipped report without performing network or browser automation."""

        return MarketplaceConnectorExecutionReport(
            connector_kind=self.connector_kind,
            status=MarketplaceConnectorStatus.SKIPPED,
            offers=[],
            error_code="connector_not_configured",
            error_message=self.reason,
        )


class MarketplaceConnectorRegistry:
    """In-process registry for backend-owned marketplace connector adapters."""

    def __init__(self) -> None:
        """Create an empty connector registry."""

        self._connectors: dict[MarketplaceConnectorKind, MarketplaceConnectorAdapter] = {}

    def register(self, connector: MarketplaceConnectorAdapter) -> None:
        """Register one connector implementation by connector kind."""

        if connector.connector_kind in self._connectors:
            raise ValueError(f"Marketplace connector {connector.connector_kind.value} is already registered.")
        self._connectors[connector.connector_kind] = connector

    def get(self, connector_kind: MarketplaceConnectorKind) -> MarketplaceConnectorAdapter | None:
        """Return a connector adapter when it is registered."""

        return self._connectors.get(connector_kind)


def build_default_marketplace_connector_registry() -> MarketplaceConnectorRegistry:
    """Build disabled placeholders for future legal marketplace integrations."""

    return build_marketplace_connector_registry(
        search_engine_discovery_enabled=False,
        search_engine_discovery_provider="disabled",
        search_engine_discovery_api_key=None,
    )


def build_marketplace_connector_registry(
    *,
    search_engine_discovery_enabled: bool,
    search_engine_discovery_provider: str,
    search_engine_discovery_api_key: str | None,
) -> MarketplaceConnectorRegistry:
    """Build connector registry from runtime settings without triggering live calls."""

    registry = MarketplaceConnectorRegistry()
    for connector_kind, reason in (
        (MarketplaceConnectorKind.KASPI, "Kaspi official API or partner feed credentials are not configured."),
        (MarketplaceConnectorKind.WILDBERRIES, "Wildberries official API or seller integration is not configured."),
        (
            MarketplaceConnectorKind.INSTAGRAM_BUSINESS,
            "Instagram Graph API business permissions are not configured.",
        ),
        (
            MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
            "Instagram public discovery is not configured; use only approved search APIs or verified sources.",
        ),
        (
            MarketplaceConnectorKind.PUBLIC_WEB_ALLOWED,
            "Approved public web discovery sources are not configured.",
        ),
    ):
        registry.register(DisabledMarketplaceConnector(connector_kind=connector_kind, reason=reason))
    registry.register(
        build_search_engine_discovery_connector(
            enabled=search_engine_discovery_enabled,
            provider=search_engine_discovery_provider,
            api_key=search_engine_discovery_api_key,
        )
    )
    return registry
