"""Orchestration for approved marketplace/open-web discovery connectors."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.marketplace_search import (
    MarketplaceConnectorExecutionReport,
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
    MarketplaceDiscoveryCandidate,
    NormalizedMarketplaceOffer,
)
from src.use_cases.similar_search.ports import SimilarSearchMarketplaceConnectorPort


class MarketplaceConnectorOrchestrationResult(BaseModel):
    """Aggregated connector result after running all requested sources."""

    model_config = ConfigDict(extra="forbid")

    reports: list[MarketplaceConnectorExecutionReport] = Field(default_factory=list)
    offers: list[NormalizedMarketplaceOffer] = Field(default_factory=list)
    candidates: list[MarketplaceDiscoveryCandidate] = Field(default_factory=list)


class MarketplaceConnectorOrchestrationService:
    """Run approved connectors while isolating one source failure from the whole search."""

    def __init__(self, *, connectors: list[SimilarSearchMarketplaceConnectorPort]) -> None:
        """Index connector adapters by kind."""

        self._connectors = {connector.connector_kind: connector for connector in connectors}

    async def search(self, *, queries: list[MarketplaceConnectorQuery]) -> MarketplaceConnectorOrchestrationResult:
        """Run configured connectors and aggregate offers, candidates, and reports."""

        reports: list[MarketplaceConnectorExecutionReport] = []
        offers: list[NormalizedMarketplaceOffer] = []
        candidates: list[MarketplaceDiscoveryCandidate] = []

        for query in queries:
            connector = self._connectors.get(query.connector_kind)
            if connector is None:
                report = _skipped_report(query.connector_kind, "Connector is not registered.")
            else:
                report = await _run_connector(connector=connector, query=query)
            reports.append(report)
            offers.extend(report.offers)
            candidates.extend(report.candidates)

        return MarketplaceConnectorOrchestrationResult(
            reports=reports,
            offers=offers,
            candidates=candidates,
        )


async def _run_connector(
    *,
    connector: SimilarSearchMarketplaceConnectorPort,
    query: MarketplaceConnectorQuery,
) -> MarketplaceConnectorExecutionReport:
    """Execute one connector and convert unexpected errors into failed reports."""

    try:
        return await connector.search(query=query)
    except Exception as exc:  # noqa: BLE001 - connector failures must be isolated.
        return MarketplaceConnectorExecutionReport(
            connector_kind=query.connector_kind,
            status=MarketplaceConnectorStatus.FAILED,
            offers=[],
            candidates=[],
            error_code="connector_execution_failed",
            error_message=str(exc),
        )


def _skipped_report(connector_kind: MarketplaceConnectorKind, reason: str) -> MarketplaceConnectorExecutionReport:
    """Return a skipped report for an unregistered connector."""

    return MarketplaceConnectorExecutionReport(
        connector_kind=connector_kind,
        status=MarketplaceConnectorStatus.SKIPPED,
        offers=[],
        candidates=[],
        error_code="connector_not_registered",
        error_message=reason,
    )
