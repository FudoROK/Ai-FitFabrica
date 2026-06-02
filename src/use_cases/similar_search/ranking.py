"""Backend-owned ranking logic for similar-search results."""

from __future__ import annotations

from src.domain.similar_search import HydratedCatalogMatch, SimilarSearchResult


def rank_similar_products(
    *,
    hydrated_products: list[HydratedCatalogMatch],
    budget_max: float | None,
    reference_price: float | None,
) -> list[SimilarSearchResult]:
    """Rank hydrated matches and mark cheaper alternatives explicitly."""
    ranked = sorted(
        hydrated_products,
        key=lambda match: _ranking_score(match=match, budget_max=budget_max, reference_price=reference_price),
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
            explanation=_build_explanation(match=match, budget_max=budget_max, reference_price=reference_price),
        )
        for match in ranked
    ]


def _ranking_score(
    *,
    match: HydratedCatalogMatch,
    budget_max: float | None,
    reference_price: float | None,
) -> float:
    score = match.similarity_score
    if budget_max is not None and match.offer.price_amount <= budget_max:
        score += 0.05
    if reference_price is not None and match.offer.price_amount < reference_price:
        score += 0.1
    if match.offer.is_available:
        score += 0.01
    return score


def _build_explanation(
    *,
    match: HydratedCatalogMatch,
    budget_max: float | None,
    reference_price: float | None,
) -> str:
    clauses = [f"Similarity {match.similarity_score:.2f}"]
    if budget_max is not None and match.offer.price_amount <= budget_max:
        clauses.append("fits budget")
    if reference_price is not None and match.offer.price_amount < reference_price:
        clauses.append("cheaper than reference")
    return ", ".join(clauses) + "."
