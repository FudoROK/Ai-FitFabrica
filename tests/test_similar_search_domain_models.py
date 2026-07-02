from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.similar_search import SimilarSearchGarmentProfile, SimilarSearchRequest, SimilarSearchResult


def test_similar_search_request_keeps_budget_and_marketplace_preferences() -> None:
    request = SimilarSearchRequest(
        source_type="text",
        query_text="black midi dress with belt",
        budget_max=120.0,
        marketplace_filters=["lamoda", "wb"],
    )

    assert request.budget_max == 120.0
    assert request.marketplace_filters == ["lamoda", "wb"]


def test_similar_search_result_exposes_cheaper_alternative_flag() -> None:
    result = SimilarSearchResult(
        product_id="product-1",
        title="Black midi dress",
        similarity_score=0.91,
        price_amount=99.0,
        currency="USD",
        marketplace="lamoda",
        is_cheaper_alternative=True,
        explanation="Lower price with close silhouette match.",
        offer_url="https://seller.example/products/product-1",
    )

    assert result.is_cheaper_alternative is True
    assert result.offer_url == "https://seller.example/products/product-1"


def test_garment_photo_request_requires_backend_garment_profile() -> None:
    with pytest.raises(ValidationError, match="garment_profile is required"):
        SimilarSearchRequest(source_type="garment_photo")


def test_garment_photo_request_keeps_backend_garment_profile() -> None:
    request = SimilarSearchRequest(
        source_type="garment_photo",
        garment_profile=SimilarSearchGarmentProfile(
            garment_type="shirt",
            dominant_color="white",
            silhouette_summary="oversized button-up shirt",
            preserved_details=["long sleeves", "front buttons"],
            confidence=0.91,
        ),
        budget_max=15000,
        user_country_code="KZ",
        user_city="Almaty",
    )

    assert request.garment_profile is not None
    assert request.garment_profile.garment_type == "shirt"
    assert request.user_city == "Almaty"
