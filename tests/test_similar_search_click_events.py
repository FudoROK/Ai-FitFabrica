from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.adapters.similar_search import InMemorySimilarSearchClickEventRepository
from src.domain.similar_search import SimilarSearchClickEventRequest
from src.use_cases.similar_search.events import SimilarSearchClickEventRejected, SimilarSearchClickEventService


@pytest.mark.asyncio
async def test_click_event_service_records_external_offer_redirect() -> None:
    repository = InMemorySimilarSearchClickEventRepository()
    service = SimilarSearchClickEventService(
        repository=repository,
        clock=lambda: datetime(2026, 7, 1, tzinfo=timezone.utc),
    )

    response = await service.record_click(
        SimilarSearchClickEventRequest(
            product_id="product-1",
            title="White shirt",
            marketplace="local_catalog",
            offer_url="https://seller.example/products/product-1",
            image_url="/api/business/products/product-1/images/primary",
            user_country_code="kz",
            user_city="Almaty",
        )
    )

    assert response.redirect_allowed is True
    assert response.redirect_url == "https://seller.example/products/product-1"
    assert len(repository.events) == 1
    assert repository.events[0].product_id == "product-1"
    assert repository.events[0].user_country_code == "KZ"


@pytest.mark.asyncio
async def test_click_event_service_records_local_only_offer_without_redirect() -> None:
    repository = InMemorySimilarSearchClickEventRepository()
    service = SimilarSearchClickEventService(repository=repository)

    response = await service.record_click(
        SimilarSearchClickEventRequest(
            product_id="product-1",
            title="White shirt",
            marketplace="local_catalog",
            offer_url="local://business-catalog/product-1",
        )
    )

    assert response.redirect_allowed is False
    assert response.redirect_url is None
    assert repository.events[0].redirect_allowed is False


@pytest.mark.asyncio
async def test_click_event_service_rejects_unsafe_offer_scheme() -> None:
    service = SimilarSearchClickEventService(repository=InMemorySimilarSearchClickEventRepository())

    with pytest.raises(SimilarSearchClickEventRejected) as exc_info:
        await service.record_click(
            SimilarSearchClickEventRequest(
                product_id="product-1",
                title="White shirt",
                marketplace="local_catalog",
                offer_url="javascript:alert(1)",
            )
        )

    assert exc_info.value.safe_code == "similar_search_offer_url_scheme_blocked"


@pytest.mark.asyncio
async def test_click_event_service_returns_aggregate_analytics() -> None:
    repository = InMemorySimilarSearchClickEventRepository()
    service = SimilarSearchClickEventService(repository=repository)

    await service.record_click(
        SimilarSearchClickEventRequest(
            product_id="product-1",
            title="White shirt",
            marketplace="local_catalog",
            offer_url="https://seller.example/products/product-1",
            user_city="Almaty",
        )
    )
    await service.record_click(
        SimilarSearchClickEventRequest(
            product_id="product-1",
            title="White shirt",
            marketplace="local_catalog",
            offer_url="local://business-catalog/product-1",
            user_city="Almaty",
        )
    )
    await service.record_click(
        SimilarSearchClickEventRequest(
            product_id="product-2",
            title="Blue shirt",
            marketplace="partner_feed",
            offer_url="https://seller.example/products/product-2",
            user_city="Astana",
        )
    )

    analytics = await service.get_analytics(limit=5)

    assert analytics.summary.total_clicks == 3
    assert analytics.summary.redirect_clicks == 2
    assert analytics.summary.local_only_clicks == 1
    assert analytics.top_products[0].key == "product-1"
    assert analytics.top_products[0].click_count == 2
    assert analytics.top_marketplaces[0].key == "local_catalog"
    assert analytics.top_cities[0].label == "Almaty"
