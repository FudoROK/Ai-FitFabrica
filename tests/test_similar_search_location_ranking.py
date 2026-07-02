from __future__ import annotations

from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord, HydratedCatalogMatch
from src.use_cases.similar_search.ranking import rank_similar_products


def test_location_first_ranking_prefers_same_city_over_cheaper_remote_offer() -> None:
    ranked = rank_similar_products(
        hydrated_products=[
            _match("remote-cheap", city="Warsaw", country_code="PL", price=5000, similarity=0.98),
            _match("same-city", city="Almaty", country_code="KZ", price=14990, similarity=0.82),
        ],
        budget_max=20000,
        reference_price=16000,
        user_country_code="KZ",
        user_city="Almaty",
    )

    assert ranked[0].product_id == "same-city"
    assert ranked[0].location_match == "same_city"
    assert ranked[0].country_code == "KZ"
    assert ranked[0].city == "Almaty"
    assert ranked[0].image_url == "/api/business/products/same-city/images/primary"
    assert "same city" in ranked[0].explanation


def test_location_first_ranking_prefers_same_country_delivery_over_remote_similarity() -> None:
    ranked = rank_similar_products(
        hydrated_products=[
            _match("remote-similar", city="Istanbul", country_code="TR", price=12000, similarity=0.96),
            _match("country-delivery", city="Astana", country_code="KZ", price=14000, similarity=0.84, delivery_regions=["Almaty"]),
        ],
        budget_max=20000,
        reference_price=16000,
        user_country_code="KZ",
        user_city="Almaty",
    )

    assert ranked[0].product_id == "country-delivery"
    assert ranked[0].location_match == "same_country_delivery"
    assert ranked[0].delivery_regions == ["Almaty"]


def _match(
    product_id: str,
    *,
    city: str,
    country_code: str,
    price: float,
    similarity: float,
    delivery_regions: list[str] | None = None,
) -> HydratedCatalogMatch:
    return HydratedCatalogMatch(
        product=CatalogProductRecord(
            product_id=product_id,
            title=f"{product_id} shirt",
            category="shirt",
            brand="local",
        ),
        offer=CatalogOfferRecord(
            offer_id=f"offer-{product_id}",
            product_id=product_id,
            marketplace="local_catalog",
            price_amount=price,
            currency="KZT",
            product_url=f"https://example.test/{product_id}",
            is_available=True,
            country_code=country_code,
            city=city,
            delivery_regions=delivery_regions or [],
            source_trust_score=0.9,
        ),
        similarity_score=similarity,
    )
