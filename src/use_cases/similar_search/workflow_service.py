"""Workflow service for backend-owned similar search."""

from __future__ import annotations

from src.domain.provider_models import EmbeddingRequest
from src.domain.similar_search import (
    HydratedCatalogMatch,
    SimilarSearchRequest,
    SimilarSearchResponse,
)
from src.domain.vector_search import VectorSearchFilter, VectorSearchQuery
from src.use_cases.similar_search.ports import (
    SimilarSearchCatalogRepositoryPort,
    SimilarSearchEmbeddingPort,
    SimilarSearchLocalCatalogSearchPort,
    SimilarSearchVectorRetrieverPort,
)
from src.use_cases.similar_search.query_preparation import build_similarity_query_profile
from src.use_cases.similar_search.ranking import rank_similar_products

_GARMENT_PHOTO_MIN_SIMILARITY = 0.62


class SimilarSearchWorkflowService:
    """Orchestrate query preparation, embeddings, retrieval, hydration, and ranking."""

    def __init__(
        self,
        *,
        embedding_provider: SimilarSearchEmbeddingPort,
        vector_retriever: SimilarSearchVectorRetrieverPort,
        catalog_repository: SimilarSearchCatalogRepositoryPort,
        local_catalog_search: SimilarSearchLocalCatalogSearchPort | None = None,
    ) -> None:
        """Store explicit boundaries for similar-search orchestration."""
        self._embedding_provider = embedding_provider
        self._vector_retriever = vector_retriever
        self._catalog_repository = catalog_repository
        self._local_catalog_search = local_catalog_search

    async def search(self, request: SimilarSearchRequest) -> SimilarSearchResponse:
        """Execute the backend-owned similar-search workflow."""
        profile = build_similarity_query_profile(request)
        embedding = self._embedding_provider.embed(
            EmbeddingRequest(
                namespace=profile.vector_namespace.value,
                input_text=profile.embedding_input,
            )
        )
        hits = self._vector_retriever.search(
            query=VectorSearchQuery(
                namespace=profile.vector_namespace,
                embedding=embedding.embedding,
                limit=request.limit,
                search_filter=VectorSearchFilter(
                    category=profile.category,
                    brand=profile.brand,
                    max_price=profile.budget_max,
                ),
            )
        )
        product_ids = [hit.owner_id for hit in hits]
        products = await self._catalog_repository.get_products_by_ids(product_ids)
        offers = await self._catalog_repository.list_offers_for_products(
            product_ids,
            marketplace_filters=profile.marketplace_filters,
        )
        product_map = {product.product_id: product for product in products}
        offers_by_product: dict[str, list[object]] = {}
        for offer in offers:
            offers_by_product.setdefault(offer.product_id, []).append(offer)

        hydrated_matches: list[HydratedCatalogMatch] = []
        for hit in hits:
            product = product_map.get(hit.owner_id)
            if product is None:
                continue
            for offer in offers_by_product.get(hit.owner_id, []):
                hydrated_matches.append(
                    HydratedCatalogMatch(
                        product=product,
                        offer=offer,
                        similarity_score=hit.score,
                    )
                )
        hydrated_matches = _filter_matches_by_category(
            matches=hydrated_matches,
            category=profile.category,
        )
        hydrated_matches = _filter_matches_by_similarity(
            matches=hydrated_matches,
            min_similarity=_minimum_similarity_for_request(request),
        )
        if not hydrated_matches and self._local_catalog_search is not None:
            hydrated_matches = await self._local_catalog_search.search_approved_matches(
                profile=profile,
                limit=request.limit,
            )
            hydrated_matches = _filter_matches_by_category(
                matches=hydrated_matches,
                category=profile.category,
            )
            hydrated_matches = _filter_matches_by_similarity(
                matches=hydrated_matches,
                min_similarity=_minimum_similarity_for_request(request),
            )

        return SimilarSearchResponse(
            results=rank_similar_products(
                hydrated_products=hydrated_matches,
                budget_max=profile.budget_max,
                reference_price=profile.reference_price,
                user_country_code=request.user_country_code,
                user_city=request.user_city,
            )
        )


def _filter_matches_by_category(*, matches: list[HydratedCatalogMatch], category: str | None) -> list[HydratedCatalogMatch]:
    """Keep garment-photo search results inside the requested garment category."""

    normalized_category = _normalize_category(category)
    if not normalized_category:
        return matches
    return [
        match
        for match in matches
        if _normalize_category(match.product.category) == normalized_category
    ]


def _filter_matches_by_similarity(*, matches: list[HydratedCatalogMatch], min_similarity: float | None) -> list[HydratedCatalogMatch]:
    """Remove weak matches before location ranking can promote them."""

    if min_similarity is None:
        return matches
    return [match for match in matches if match.similarity_score >= min_similarity]


def _minimum_similarity_for_request(request: SimilarSearchRequest) -> float | None:
    """Return the minimum acceptable match score for visual garment searches."""

    if request.source_type == "garment_photo":
        return _GARMENT_PHOTO_MIN_SIMILARITY
    return None


def _normalize_category(value: str | None) -> str:
    """Normalize catalog and agent category labels for conservative matching."""

    return (value or "").strip().casefold()
