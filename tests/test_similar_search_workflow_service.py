from __future__ import annotations

import pytest

from src.domain.provider_models import EmbeddingRequest, EmbeddingResult
from src.domain.similar_search import (
    CatalogOfferRecord,
    CatalogProductRecord,
    HydratedCatalogMatch,
    SimilarSearchGarmentProfile,
    SimilarSearchRequest,
    SimilarityQueryProfile,
)
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


class _EmptyVectorRetriever:
    def search(self, *, query):
        return []


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


class _MismatchedCategoryCatalogRepository:
    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        return [
            CatalogProductRecord(
                product_id="product-1",
                title="Olive quilted jacket",
                category="outerwear",
                brand="local boutique",
                color="olive",
            )
        ]

    async def list_offers_for_products(self, product_ids: list[str], *, marketplace_filters: list[str]) -> list[CatalogOfferRecord]:
        return [
            CatalogOfferRecord(
                offer_id="offer-1",
                product_id="product-1",
                marketplace="local_catalog",
                price_amount=45900.0,
                currency="KZT",
                product_url="https://example.test/jacket-1",
                is_available=True,
                country_code="KZ",
                city="Almaty",
                delivery_regions=["Almaty"],
                source_trust_score=0.85,
            )
        ]


class _LocalCatalogFallback:
    async def search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
    ) -> list[HydratedCatalogMatch]:
        return [
            HydratedCatalogMatch(
                product=CatalogProductRecord(
                    product_id="local-shirt-1",
                    title="White oversized shirt",
                    category="shirt",
                    brand="local boutique",
                    color="white",
                ),
                offer=CatalogOfferRecord(
                    offer_id="offer-local-shirt-1",
                    product_id="local-shirt-1",
                    marketplace="local_catalog",
                    price_amount=14990.0,
                    currency="KZT",
                    product_url="https://example.test/local-shirt-1",
                    country_code="KZ",
                    city="Almaty",
                    delivery_regions=["Almaty", "Astana"],
                    source_trust_score=0.85,
                ),
                similarity_score=0.74,
            )
        ]


class _WrongCategoryLocalCatalogFallback:
    async def search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
    ) -> list[HydratedCatalogMatch]:
        return [
            HydratedCatalogMatch(
                product=CatalogProductRecord(
                    product_id="local-jacket-1",
                    title="Olive quilted jacket",
                    category="outerwear",
                    brand="local boutique",
                    color="olive",
                ),
                offer=CatalogOfferRecord(
                    offer_id="offer-local-jacket-1",
                    product_id="local-jacket-1",
                    marketplace="local_catalog",
                    price_amount=45900.0,
                    currency="KZT",
                    product_url="https://example.test/local-jacket-1",
                    country_code="KZ",
                    city="Almaty",
                    delivery_regions=["Almaty", "Astana"],
                    source_trust_score=0.85,
                ),
                similarity_score=0.58,
            )
        ]


class _WeakSameCategoryLocalCatalogFallback:
    async def search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
    ) -> list[HydratedCatalogMatch]:
        return [
            HydratedCatalogMatch(
                product=CatalogProductRecord(
                    product_id="weak-shirt-1",
                    title="Generic white shirt",
                    category="shirt",
                    brand="local boutique",
                    color="white",
                ),
                offer=CatalogOfferRecord(
                    offer_id="offer-weak-shirt-1",
                    product_id="weak-shirt-1",
                    marketplace="local_catalog",
                    price_amount=9900.0,
                    currency="KZT",
                    product_url="https://example.test/weak-shirt-1",
                    country_code="KZ",
                    city="Almaty",
                    delivery_regions=["Almaty"],
                    source_trust_score=0.85,
                ),
                similarity_score=0.58,
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


@pytest.mark.asyncio
async def test_workflow_service_falls_back_to_local_catalog_when_vector_index_is_empty() -> None:
    service = SimilarSearchWorkflowService(
        embedding_provider=_EmbeddingProvider(),
        vector_retriever=_EmptyVectorRetriever(),
        catalog_repository=_CatalogRepository(),
        local_catalog_search=_LocalCatalogFallback(),
    )

    response = await service.search(
        SimilarSearchRequest(
            source_type="garment_photo",
            garment_profile=SimilarSearchGarmentProfile(
                garment_type="shirt",
                dominant_color="white",
                silhouette_summary="oversized button-up shirt",
                preserved_details=["long sleeves", "front buttons"],
                confidence=0.91,
            ),
            budget_max=20000,
            user_country_code="KZ",
            user_city="Almaty",
        )
    )

    assert [result.product_id for result in response.results] == ["local-shirt-1"]
    assert response.results[0].location_match == "same_city"
    assert response.results[0].country_code == "KZ"
    assert response.results[0].city == "Almaty"
    assert response.results[0].delivery_regions == ["Almaty", "Astana"]


@pytest.mark.asyncio
async def test_workflow_service_filters_vector_hits_from_wrong_garment_category_before_location_ranking() -> None:
    service = SimilarSearchWorkflowService(
        embedding_provider=_EmbeddingProvider(),
        vector_retriever=_VectorRetriever(),
        catalog_repository=_MismatchedCategoryCatalogRepository(),
        local_catalog_search=_LocalCatalogFallback(),
    )

    response = await service.search(
        SimilarSearchRequest(
            source_type="garment_photo",
            garment_profile=SimilarSearchGarmentProfile(
                garment_type="shirt",
                dominant_color="white",
                silhouette_summary="oversized button-up shirt",
                preserved_details=["long sleeves", "front buttons"],
                confidence=0.91,
            ),
            user_country_code="KZ",
            user_city="Almaty",
        )
    )

    assert [result.product_id for result in response.results] == ["local-shirt-1"]


@pytest.mark.asyncio
async def test_workflow_service_filters_wrong_category_local_fallback_results_for_garment_photo() -> None:
    service = SimilarSearchWorkflowService(
        embedding_provider=_EmbeddingProvider(),
        vector_retriever=_EmptyVectorRetriever(),
        catalog_repository=_CatalogRepository(),
        local_catalog_search=_WrongCategoryLocalCatalogFallback(),
    )

    response = await service.search(
        SimilarSearchRequest(
            source_type="garment_photo",
            garment_profile=SimilarSearchGarmentProfile(
                garment_type="shirt",
                dominant_color="white",
                silhouette_summary="oversized button-up shirt",
                preserved_details=["long sleeves", "front buttons"],
                confidence=0.91,
            ),
            user_country_code="KZ",
            user_city="Almaty",
        )
    )

    assert response.results == []


@pytest.mark.asyncio
async def test_workflow_service_filters_weak_local_fallback_similarity_for_garment_photo() -> None:
    service = SimilarSearchWorkflowService(
        embedding_provider=_EmbeddingProvider(),
        vector_retriever=_EmptyVectorRetriever(),
        catalog_repository=_CatalogRepository(),
        local_catalog_search=_WeakSameCategoryLocalCatalogFallback(),
    )

    response = await service.search(
        SimilarSearchRequest(
            source_type="garment_photo",
            garment_profile=SimilarSearchGarmentProfile(
                garment_type="shirt",
                dominant_color="white",
                silhouette_summary="oversized button-up shirt",
                preserved_details=["long sleeves", "front buttons"],
                confidence=0.91,
            ),
            user_country_code="KZ",
            user_city="Almaty",
        )
    )

    assert response.results == []
