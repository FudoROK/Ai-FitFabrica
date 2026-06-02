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
    SimilarSearchVectorRetrieverPort,
)
from src.use_cases.similar_search.query_preparation import build_similarity_query_profile
from src.use_cases.similar_search.ranking import rank_similar_products


class SimilarSearchWorkflowService:
    """Orchestrate query preparation, embeddings, retrieval, hydration, and ranking."""

    def __init__(
        self,
        *,
        embedding_provider: SimilarSearchEmbeddingPort,
        vector_retriever: SimilarSearchVectorRetrieverPort,
        catalog_repository: SimilarSearchCatalogRepositoryPort,
    ) -> None:
        """Store explicit boundaries for similar-search orchestration."""
        self._embedding_provider = embedding_provider
        self._vector_retriever = vector_retriever
        self._catalog_repository = catalog_repository

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

        return SimilarSearchResponse(
            results=rank_similar_products(
                hydrated_products=hydrated_matches,
                budget_max=profile.budget_max,
                reference_price=profile.reference_price,
            )
        )
