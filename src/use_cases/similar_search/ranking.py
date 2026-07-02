"""Backend-owned ranking logic for similar-search results."""

from __future__ import annotations

from src.domain.similar_search import HydratedCatalogMatch, SimilarSearchResult
from src.use_cases.similar_search.location_ranking import (
    classify_location_match,
    location_explanation,
    location_priority,
)


def rank_similar_products(
    *,
    hydrated_products: list[HydratedCatalogMatch],
    budget_max: float | None,
    reference_price: float | None,
    user_country_code: str | None = None,
    user_city: str | None = None,
) -> list[SimilarSearchResult]:
    """Rank hydrated matches and mark cheaper alternatives explicitly."""
    ranked = sorted(
        hydrated_products,
        key=lambda match: _ranking_score(
            match=match,
            budget_max=budget_max,
            reference_price=reference_price,
            user_country_code=user_country_code,
            user_city=user_city,
        ),
        reverse=True,
    )
    return [
        SimilarSearchResult(
            product_id=match.product.product_id,
            title=match.product.title,
            similarity_score=match.similarity_score,
            price_amount=match.offer.price_amount,
            currency=match.offer.currency,
            marketplace=match.offer.marketplace,
            is_cheaper_alternative=reference_price is not None and match.offer.price_amount < reference_price,
            explanation=_build_explanation(
                match=match,
                budget_max=budget_max,
                reference_price=reference_price,
                user_country_code=user_country_code,
                user_city=user_city,
            ),
            location_match=classify_location_match(
                offer=match.offer,
                user_country_code=user_country_code,
                user_city=user_city,
            ),
            country_code=match.offer.country_code,
            city=match.offer.city,
            delivery_regions=match.offer.delivery_regions,
            image_url=f"/api/business/products/{match.product.product_id}/images/primary",
            offer_url=match.offer.product_url,
        )
        for match in ranked
    ]


def _ranking_score(
    *,
    match: HydratedCatalogMatch,
    budget_max: float | None,
    reference_price: float | None,
    user_country_code: str | None,
    user_city: str | None,
) -> float:
    location_match = classify_location_match(
        offer=match.offer,
        user_country_code=user_country_code,
        user_city=user_city,
    )
    score = float(location_priority(location_match))
    score += min(max(match.similarity_score, 0.0), 1.0) * 0.1
    if budget_max is not None and match.offer.price_amount <= budget_max:
        score += 0.03
    if reference_price is not None and match.offer.price_amount < reference_price:
        score += 0.04
    if match.offer.is_available:
        score += 0.01
    score += match.offer.source_trust_score * 0.02
    return score


def _build_explanation(
    *,
    match: HydratedCatalogMatch,
    budget_max: float | None,
    reference_price: float | None,
    user_country_code: str | None,
    user_city: str | None,
) -> str:
    location_match = classify_location_match(
        offer=match.offer,
        user_country_code=user_country_code,
        user_city=user_city,
    )
    clauses = [location_explanation(location_match), f"similarity {match.similarity_score:.2f}"]
    if budget_max is not None and match.offer.price_amount <= budget_max:
        clauses.append("fits budget")
    if reference_price is not None and match.offer.price_amount < reference_price:
        clauses.append("cheaper than reference")
    return ", ".join(clauses) + "."
