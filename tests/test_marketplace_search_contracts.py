from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.marketplace_search import (
    MarketplaceConnectorExecutionReport,
    MarketplaceConnectorKind,
    MarketplaceConnectorQuery,
    MarketplaceConnectorStatus,
    MarketplaceDiscoveryCandidate,
    MarketplaceDiscoveryCandidateStatus,
    MarketplaceLegalAccessType,
    MarketplaceSearchSourcePolicy,
    MarketplaceSourceType,
    NormalizedMarketplaceOffer,
)
from src.use_cases.similar_search.ports import SimilarSearchMarketplaceConnectorPort


def test_normalized_marketplace_offer_accepts_approved_source_types() -> None:
    offer = NormalizedMarketplaceOffer(
        source_type=MarketplaceSourceType.LOCAL_CATALOG,
        source_id="local-catalog",
        product_id="product-1",
        title="White shirt",
        category="shirt",
        price_amount=14990,
        currency="KZT",
        country_code="KZ",
        city="Almaty",
        delivery_regions=["Astana"],
        product_url="https://example.test/product-1",
        is_available=True,
        source_trust_score=0.9,
    )

    assert offer.source_type is MarketplaceSourceType.LOCAL_CATALOG
    assert offer.delivery_regions == ["Astana"]


def test_normalized_marketplace_offer_rejects_unknown_source_type() -> None:
    with pytest.raises(ValidationError):
        NormalizedMarketplaceOffer(
            source_type="hidden_scraper",
            source_id="scraper",
            product_id="product-1",
            title="White shirt",
            category="shirt",
            price_amount=14990,
            currency="KZT",
            country_code="KZ",
            city="Almaty",
            product_url="https://example.test/product-1",
            source_trust_score=0.1,
        )


def test_marketplace_source_policy_blocks_hidden_scraping() -> None:
    policy = MarketplaceSearchSourcePolicy()

    assert policy.is_allowed(MarketplaceSourceType.OFFICIAL_API) is True
    assert policy.is_allowed(MarketplaceSourceType.PUBLIC_WEB_ALLOWED) is True
    assert policy.is_allowed(MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY) is True
    assert policy.is_disallowed_source_name("hidden_scraping") is True
    assert policy.is_disallowed_source_name("browser_automation") is True


def test_marketplace_connector_query_requires_location_and_approved_legal_access() -> None:
    query = MarketplaceConnectorQuery(
        connector_kind=MarketplaceConnectorKind.KASPI,
        source_type=MarketplaceSourceType.OFFICIAL_API,
        legal_access_type=MarketplaceLegalAccessType.OFFICIAL_API,
        user_country_code="KZ",
        user_city="Almaty",
        category="shirt",
        normalized_terms=["white shirt", "button up"],
        limit=20,
    )

    assert query.connector_kind is MarketplaceConnectorKind.KASPI
    assert query.user_city == "Almaty"
    assert query.normalized_terms == ["white shirt", "button up"]


def test_marketplace_connector_query_rejects_hidden_scraping_access() -> None:
    with pytest.raises(ValidationError):
        MarketplaceConnectorQuery(
            connector_kind=MarketplaceConnectorKind.WILDBERRIES,
            source_type=MarketplaceSourceType.OFFICIAL_API,
            legal_access_type="hidden_scraping",
            user_country_code="KZ",
            user_city="Astana",
            category="outerwear",
            normalized_terms=["olive jacket"],
        )


def test_marketplace_connector_query_accepts_search_engine_discovery_source() -> None:
    query = MarketplaceConnectorQuery(
        connector_kind=MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        legal_access_type=MarketplaceLegalAccessType.SEARCH_ENGINE_API,
        user_country_code="KZ",
        user_city="Almaty",
        category="shirt",
        normalized_terms=["white shirt Almaty"],
    )

    assert query.connector_kind is MarketplaceConnectorKind.SEARCH_ENGINE_DISCOVERY
    assert query.source_type is MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY


def test_instagram_public_discovery_candidate_is_not_a_normalized_offer() -> None:
    candidate = MarketplaceDiscoveryCandidate(
        candidate_id="instagram-candidate-1",
        connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
        source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
        source_url="https://www.instagram.com/example_shop/p/example",
        source_title="Example shop white shirt",
        source_snippet="White shirt available in Almaty. DM for price.",
        platform_hint="instagram",
        category="shirt",
        country_code="KZ",
        city="Almaty",
        status=MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW,
    )

    assert candidate.status is MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW
    assert candidate.requires_review is True
    assert candidate.platform_hint == "instagram"


def test_connector_report_can_return_discovery_candidates_without_sellable_offers() -> None:
    report = MarketplaceConnectorExecutionReport(
        connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
        status=MarketplaceConnectorStatus.SUCCEEDED,
        offers=[],
        candidates=[
            MarketplaceDiscoveryCandidate(
                candidate_id="instagram-candidate-1",
                connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
                source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
                source_url="https://www.instagram.com/example_shop/p/example",
                source_title="Example shop white shirt",
                platform_hint="instagram",
                category="shirt",
                status=MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW,
            )
        ],
    )

    assert report.is_successful is True
    assert report.offers == []
    assert report.candidates[0].requires_review is True


def test_marketplace_connector_execution_report_isolates_failures_and_no_results() -> None:
    no_result_report = MarketplaceConnectorExecutionReport(
        connector_kind=MarketplaceConnectorKind.INSTAGRAM_BUSINESS,
        status=MarketplaceConnectorStatus.NO_RESULTS,
        offers=[],
        error_code=None,
        error_message=None,
    )
    failed_report = MarketplaceConnectorExecutionReport(
        connector_kind=MarketplaceConnectorKind.KASPI,
        status=MarketplaceConnectorStatus.FAILED,
        offers=[],
        error_code="connector_timeout",
        error_message="Connector timed out.",
    )

    assert no_result_report.is_successful is True
    assert failed_report.is_successful is False
    assert failed_report.error_code == "connector_timeout"


def test_similar_search_marketplace_connector_port_is_backend_owned_contract() -> None:
    assert hasattr(SimilarSearchMarketplaceConnectorPort, "search")
