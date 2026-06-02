from __future__ import annotations

from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord, HydratedCatalogMatch
from src.use_cases.similar_search.ranking import rank_similar_products


def test_ranking_prefers_high_similarity_then_marks_cheaper_alternative() -> None:
    ranked = rank_similar_products(
        hydrated_products=[
            HydratedCatalogMatch(
                product=CatalogProductRecord(
                    product_id="product-1",
                    title="Black midi dress",
                    category="dress",
                    brand="zara",
                    color="black",
                ),
                offer=CatalogOfferRecord(
                    offer_id="offer-1",
                    product_id="product-1",
                    marketplace="lamoda",
                    price_amount=99.0,
                    currency="USD",
                    product_url="https://example.test/offer-1",
                    is_available=True,
                ),
                similarity_score=0.91,
            ),
            HydratedCatalogMatch(
                product=CatalogProductRecord(
                    product_id="product-2",
                    title="Black dress alt",
                    category="dress",
                    brand="mango",
                    color="black",
                ),
                offer=CatalogOfferRecord(
                    offer_id="offer-2",
                    product_id="product-2",
                    marketplace="wb",
                    price_amount=150.0,
                    currency="USD",
                    product_url="https://example.test/offer-2",
                    is_available=True,
                ),
                similarity_score=0.89,
            ),
        ],
        budget_max=120.0,
        reference_price=160.0,
    )

    assert ranked[0].is_cheaper_alternative is True
    assert ranked[0].product_id == "product-1"
