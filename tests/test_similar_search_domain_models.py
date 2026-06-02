from __future__ import annotations

from src.domain.similar_search import SimilarSearchRequest, SimilarSearchResult


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
    )

    assert result.is_cheaper_alternative is True
