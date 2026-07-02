from __future__ import annotations

import pytest

from src.domain.marketplace_search import (
    MarketplaceConnectorExecutionReport,
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
    MarketplaceDiscoveryCandidate,
    MarketplaceLegalAccessType,
    MarketplaceSourceType,
    NormalizedMarketplaceOffer,
)
from src.use_cases.similar_search.marketplace_orchestration import (
    MarketplaceConnectorOrchestrationService,
)


def _query(kind: MarketplaceConnectorKind) -> MarketplaceConnectorQuery:
    return MarketplaceConnectorQuery(
        connector_kind=kind,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        legal_access_type=MarketplaceLegalAccessType.SEARCH_ENGINE_API,
        user_country_code="KZ",
        user_city="Almaty",
        category="shirt",
        normalized_terms=["white shirt Almaty"],
    )


class _CandidateConnector:
    connector_kind = MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        return MarketplaceConnectorExecutionReport(
            connector_kind=self.connector_kind,
            status=MarketplaceConnectorStatus.SUCCEEDED,
            candidates=[
                MarketplaceDiscoveryCandidate(
                    candidate_id="instagram-candidate-1",
                    connector_kind=self.connector_kind,
                    source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
                    source_url="https://www.instagram.com/example_shop/p/example",
                    source_title="Example shop white shirt",
                    platform_hint="instagram",
                    category=query.category,
                    country_code=query.user_country_code,
                    city=query.user_city,
                )
            ],
        )


class _OfferConnector:
    connector_kind = MarketplaceConnectorKind.PARTNER_FEED

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        return MarketplaceConnectorExecutionReport(
            connector_kind=self.connector_kind,
            status=MarketplaceConnectorStatus.SUCCEEDED,
            offers=[
                NormalizedMarketplaceOffer(
                    source_type=MarketplaceSourceType.PARTNER_FEED,
                    source_id="partner-feed-1",
                    product_id="partner-shirt-1",
                    title="Partner white shirt",
                    category=query.category,
                    price_amount=14990,
                    currency="KZT",
                    country_code=query.user_country_code,
                    city=query.user_city,
                    product_url="https://example.test/partner-shirt-1",
                    source_trust_score=0.8,
                )
            ],
        )


class _FailingConnector:
    connector_kind = MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        raise RuntimeError("search provider unavailable")


@pytest.mark.asyncio
async def test_marketplace_orchestration_collects_offers_candidates_and_failed_reports() -> None:
    service = MarketplaceConnectorOrchestrationService(
        connectors=[_CandidateConnector(), _OfferConnector(), _FailingConnector()]
    )

    result = await service.search(
        queries=[
            _query(MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY),
            _query(MarketplaceConnectorKind.PARTNER_FEED),
            _query(MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY),
        ]
    )

    assert [offer.product_id for offer in result.offers] == ["partner-shirt-1"]
    assert [candidate.candidate_id for candidate in result.candidates] == ["instagram-candidate-1"]
    assert [report.status for report in result.reports] == [
        MarketplaceConnectorStatus.SUCCEEDED,
        MarketplaceConnectorStatus.SUCCEEDED,
        MarketplaceConnectorStatus.FAILED,
    ]
