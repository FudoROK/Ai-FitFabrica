from __future__ import annotations

from decimal import Decimal

import pytest

from src.domain.provider_models import EmbeddingRequest, EmbeddingResult
from src.domain.vector_search import VectorNamespace, VectorPointRecord
from src.use_cases.business_catalog.search_indexing import BusinessCatalogSearchIndexingService
from src.use_cases.business_catalog.search_projection import BusinessCatalogSearchRecord


class _EmbeddingProvider:
    def __init__(self) -> None:
        self.requests: list[EmbeddingRequest] = []

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        self.requests.append(request)
        return EmbeddingResult(
            namespace=request.namespace,
            embedding=[0.1, 0.2, 0.3],
            provider="fake_embedding",
            model="fake-embedding-v1",
        )


class _VectorIndex:
    def __init__(self) -> None:
        self.records: list[VectorPointRecord] = []

    def upsert_points(self, *, records: list[VectorPointRecord]) -> None:
        self.records.extend(records)


class _VectorBootstrapper:
    def __init__(self) -> None:
        self.namespaces: list[VectorNamespace] = []

    def ensure_collection(self, *, namespace: VectorNamespace) -> None:
        self.namespaces.append(namespace)


@pytest.mark.asyncio
async def test_search_indexing_service_upserts_approved_catalog_records() -> None:
    embedding_provider = _EmbeddingProvider()
    vector_index = _VectorIndex()
    service = BusinessCatalogSearchIndexingService(
        embedding_provider=embedding_provider,
        vector_index=vector_index,
    )

    result = await service.index_records([_record()])

    assert result.indexed_count == 1
    assert result.skipped_count == 0
    assert embedding_provider.requests[0].namespace == VectorNamespace.PRODUCTS.value
    assert "White oversized shirt" in embedding_provider.requests[0].input_text
    assert "Almaty" in embedding_provider.requests[0].input_text
    assert vector_index.records == [
        VectorPointRecord(
            point_id="business-catalog:product_1",
            namespace=VectorNamespace.PRODUCTS,
            embedding=[0.1, 0.2, 0.3],
            owner_id="product_1",
            payload={
                "product_id": "product_1",
                "merchant_id": "merchant_1",
                "category": "shirt",
                "city": "Almaty",
                "country_code": "KZ",
                "currency": "KZT",
                "price_amount": 14990.0,
                "marketplace_source_type": "local_catalog",
                "source_trust_score": 0.85,
            },
        )
    ]


@pytest.mark.asyncio
async def test_search_indexing_service_bootstraps_products_collection_before_upsert() -> None:
    embedding_provider = _EmbeddingProvider()
    vector_index = _VectorIndex()
    bootstrapper = _VectorBootstrapper()
    service = BusinessCatalogSearchIndexingService(
        embedding_provider=embedding_provider,
        vector_index=vector_index,
        vector_bootstrapper=bootstrapper,
    )

    await service.index_records([_record()])

    assert bootstrapper.namespaces == [VectorNamespace.PRODUCTS]
    assert len(vector_index.records) == 1


def _record() -> BusinessCatalogSearchRecord:
    return BusinessCatalogSearchRecord(
        product_id="product_1",
        merchant_id="merchant_1",
        owner_id="owner_1",
        title="White oversized shirt",
        category="shirt",
        description="Lightweight cotton shirt with buttons.",
        country_code="KZ",
        city="Almaty",
        source_type="manual",
        price_amount=Decimal("14990"),
        currency="KZT",
        availability="in_stock",
        product_url="https://example.com/product",
        delivery_regions=["Almaty", "Astana"],
        marketplace_source_type="local_catalog",
        source_trust_score=0.85,
    )
