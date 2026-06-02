"""Prepare backend-owned similar-search query profiles."""

from __future__ import annotations

from src.domain.similar_search import SimilarSearchRequest, SimilarityQueryProfile


def build_similarity_query_profile(request: SimilarSearchRequest) -> SimilarityQueryProfile:
    """Convert an external request into a normalized backend retrieval profile."""
    embedding_input = (request.query_text or "").strip()
    if request.source_type == "product_ref":
        embedding_input = f"product:{request.product_id}"

    return SimilarityQueryProfile(
        embedding_input=embedding_input,
        budget_max=request.budget_max,
        marketplace_filters=list(request.marketplace_filters),
        category=request.category,
        brand=request.brand,
        reference_price=request.reference_price,
    )
