"""Mapping helpers for Qdrant payload filters."""

from __future__ import annotations

from src.domain.vector_search import VectorSearchFilter


def build_qdrant_filter(search_filter: VectorSearchFilter | None) -> dict[str, list[dict[str, object]]] | None:
    """Convert typed backend filter data into a Qdrant-compatible payload shape."""
    if search_filter is None:
        return None

    must: list[dict[str, object]] = []
    if search_filter.category:
        must.append({"key": "category", "match": {"value": search_filter.category}})
    if search_filter.brand:
        must.append({"key": "brand", "match": {"value": search_filter.brand}})
    if search_filter.min_price is not None or search_filter.max_price is not None:
        price_range: dict[str, float] = {}
        if search_filter.min_price is not None:
            price_range["gte"] = search_filter.min_price
        if search_filter.max_price is not None:
            price_range["lte"] = search_filter.max_price
        must.append({"key": "price", "range": price_range})

    if not must:
        return None
    return {"must": must}
