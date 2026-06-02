"""Tests for mapping typed retrieval filters into Qdrant payload filters."""

from __future__ import annotations

from src.adapters.vector.qdrant_filters import build_qdrant_filter
from src.domain.vector_search import VectorSearchFilter


def test_filter_builder_maps_category_brand_and_price_bounds() -> None:
    """Typed backend filters must be converted into a payload filter shape."""
    payload_filter = build_qdrant_filter(
        VectorSearchFilter(
            category="dress",
            brand="zara",
            min_price=100,
            max_price=300,
        )
    )

    assert payload_filter is not None
    assert payload_filter["must"][0] == {"key": "category", "match": {"value": "dress"}}
    assert payload_filter["must"][1] == {"key": "brand", "match": {"value": "zara"}}
    assert payload_filter["must"][2] == {"key": "price", "range": {"gte": 100, "lte": 300}}


def test_filter_builder_returns_none_for_empty_filter() -> None:
    """No payload conditions should produce no Qdrant filter."""
    payload_filter = build_qdrant_filter(VectorSearchFilter())

    assert payload_filter is None
