from __future__ import annotations

import pytest

from src.domain.provider_models import EmbeddingRequest, EmbeddingResult
from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord, SimilarSearchRequest
from src.domain.vector_search import VectorNamespace, VectorSearchHit
from src.use_cases.similar_search.workflow_service import SimilarSearchWorkflowService


class _EmbeddingProvider:
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            namespace=request.namespace,
            embedding=[0.1, 0.2, 0.3],
            provider="fake_embedding",
            model="fake-embedding-v1",
        )


class _VectorRetriever:
    def search(self, *, query):
        return [
            VectorSearchHit(
                point_id="vector-1",
                owner_id="product-1",
                namespace=VectorNamespace.PRODUCTS,
                score=0.91,
                payload={"category": "dress", "brand": "zara"},
            )
        ]


class _CatalogRepository:
    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        return [
            CatalogProductRecord(
                product_id="product-1",
                title="Black midi dress",
                category="dress",
                brand="zara",
                color="black",
            )
        ]

    async def list_offers_for_products(self, product_ids: list[str], *, marketplace_filters: list[str]) -> list[CatalogOfferRecord]:
        return [
            CatalogOfferRecord(
                offer_id="offer-1",
                product_id="product-1",
                marketplace="lamoda",
                price_amount=99.0,
                currency="USD",
                product_url="https://example.test/offer-1",
                is_available=True,
            )
        ]


@pytest.mark.asyncio
async def test_workflow_service_embeds_queries_retrieves_hits_and_returns_ranked_results() -> None:
    service = SimilarSearchWorkflowService(
        embedding_provider=_EmbeddingProvider(),
        vector_retriever=_VectorRetriever(),
        catalog_repository=_CatalogRepository(),
    )

    response = await service.search(
        SimilarSearchRequest(
            source_type="text",
            query_text="black midi dress with belt",
            budget_max=120.0,
            reference_price=150.0,
        )
    )

    assert response.results
    assert response.results[0].product_id == "product-1"
