"""Prepare backend-owned similar-search query profiles."""

from __future__ import annotations

from src.domain.garment_category import canonicalize_garment_category
from src.domain.similar_search import SimilarSearchRequest, SimilarityQueryProfile


def build_similarity_query_profile(request: SimilarSearchRequest) -> SimilarityQueryProfile:
    """Convert an external request into a normalized backend retrieval profile."""
    embedding_input = (request.query_text or "").strip()
    if request.source_type == "product_ref":
        embedding_input = f"product:{request.product_id}"
    if request.source_type == "garment_photo" and request.garment_profile is not None:
        embedding_input = _garment_profile_embedding_input(request)

    raw_category = request.category or (request.garment_profile.garment_type if request.garment_profile else None)
    return SimilarityQueryProfile(
        embedding_input=embedding_input,
        budget_max=request.budget_max,
        marketplace_filters=list(request.marketplace_filters),
        category=canonicalize_garment_category(raw_category),
        brand=request.brand,
        reference_price=request.reference_price,
    )


def _garment_profile_embedding_input(request: SimilarSearchRequest) -> str:
    """Create one stable search phrase from backend-approved garment facts."""
    profile = request.garment_profile
    if profile is None:
        return ""
    parts = [
        f"garment_type: {profile.garment_type}",
        f"color: {profile.dominant_color}",
    ]
    if profile.secondary_colors:
        parts.append(f"secondary_colors: {', '.join(profile.secondary_colors)}")
    parts.append(f"silhouette: {profile.silhouette_summary}")
    if profile.preserved_details:
        parts.append(f"details: {', '.join(profile.preserved_details)}")
    return "; ".join(parts)

