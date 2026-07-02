"""Tests for the first Qdrant retriever adapter."""

from __future__ import annotations

from uuid import UUID

from src.adapters.vector.qdrant_retriever import QdrantVectorRetriever
from src.domain.vector_search import (
    VectorNamespace,
    VectorPointRecord,
    VectorSearchFilter,
    VectorSearchHit,
    VectorSearchQuery,
)


class FakeQdrantClient:
    """Local fake client for retriever behavior tests."""

    def __init__(self) -> None:
        self.upsert_calls: list[dict[str, object]] = []
        self.search_calls: list[dict[str, object]] = []

    def upsert(self, **kwargs: object) -> None:
        self.upsert_calls.append(kwargs)

    def search(self, **kwargs: object) -> list[dict[str, object]]:
        self.search_calls.append(kwargs)
        return [
            {
                "id": "garment-1",
                "score": 0.91,
                "payload": {
                    "owner_id": "product-123",
                    "category": "dress",
                    "brand": "zara",
                },
            }
        ]


class MissingCollectionQdrantClient:
    """Fake Qdrant client that behaves like an uninitialized collection."""

    def search(self, **kwargs: object) -> list[dict[str, object]]:
        raise _MissingCollectionUnexpectedResponse()


class ObjectHitQdrantClient:
    """Fake client that returns object-like hits like the real Qdrant client."""

    def search(self, **kwargs: object) -> list[object]:
        return [
            type(
                "ScoredPoint",
                (),
                {
                    "id": "6d2c4d1b-0cb3-5db8-a73c-49f15d53b718",
                    "score": 0.88,
                    "payload": {
                        "point_id": "business-catalog:product_1",
                        "owner_id": "product_1",
                        "category": "shirt",
                    },
                },
            )()
        ]


class _MissingCollectionUnexpectedResponse(Exception):
    status_code = 404
    content = b'{"status":{"error":"Not found: Collection `fitfabrica_products` doesn\\\'t exist!"}}'

    def __str__(self) -> str:
        return "Unexpected Response: 404 (Not Found)"


def test_retriever_upserts_records_into_namespace_collection() -> None:
    """Retriever must write vector points into the namespace collection."""
    client = FakeQdrantClient()
    retriever = QdrantVectorRetriever(client=client, collection_prefix="fitfabrica")

    retriever.upsert_points(
        records=[
            VectorPointRecord(
                point_id="garment-1",
                namespace=VectorNamespace.GARMENTS,
                embedding=[0.1, 0.2, 0.3],
                payload={"category": "dress", "brand": "zara"},
                owner_id="product-123",
            )
        ]
    )

    assert client.upsert_calls[0]["collection_name"] == "fitfabrica_garments"


def test_retriever_maps_domain_point_id_to_stable_qdrant_uuid() -> None:
    """Qdrant point IDs must be UUID-compatible while preserving domain IDs."""
    client = FakeQdrantClient()
    retriever = QdrantVectorRetriever(client=client, collection_prefix="fitfabrica")

    retriever.upsert_points(
        records=[
            VectorPointRecord(
                point_id="business-catalog:product_1",
                namespace=VectorNamespace.PRODUCTS,
                embedding=[0.1, 0.2, 0.3],
                payload={"product_id": "product_1"},
                owner_id="product_1",
            )
        ]
    )

    point = client.upsert_calls[0]["points"][0]

    assert UUID(str(point["id"]))
    assert point["payload"]["point_id"] == "business-catalog:product_1"


def test_retriever_search_returns_typed_hits() -> None:
    """Retriever must return typed similarity hits, not raw client data."""
    client = FakeQdrantClient()
    retriever = QdrantVectorRetriever(client=client, collection_prefix="fitfabrica")

    hits = retriever.search(
        query=VectorSearchQuery(
            namespace=VectorNamespace.GARMENTS,
            embedding=[0.1, 0.2, 0.3],
            limit=5,
            search_filter=VectorSearchFilter(category="dress"),
        )
    )

    assert hits == [
        VectorSearchHit(
            point_id="garment-1",
            owner_id="product-123",
            namespace=VectorNamespace.GARMENTS,
            score=0.91,
            payload={"owner_id": "product-123", "category": "dress", "brand": "zara"},
        )
    ]


def test_retriever_search_maps_real_qdrant_object_hits() -> None:
    """Retriever must support real qdrant-client ScoredPoint-like hits."""
    retriever = QdrantVectorRetriever(client=ObjectHitQdrantClient(), collection_prefix="fitfabrica")

    hits = retriever.search(
        query=VectorSearchQuery(
            namespace=VectorNamespace.PRODUCTS,
            embedding=[0.1, 0.2, 0.3],
            limit=5,
        )
    )

    assert hits == [
        VectorSearchHit(
            point_id="business-catalog:product_1",
            owner_id="product_1",
            namespace=VectorNamespace.PRODUCTS,
            score=0.88,
            payload={
                "point_id": "business-catalog:product_1",
                "owner_id": "product_1",
                "category": "shirt",
            },
        )
    ]


def test_retriever_returns_empty_hits_when_collection_is_not_created_yet() -> None:
    """Missing vector collection must not block local catalog fallback."""
    retriever = QdrantVectorRetriever(client=MissingCollectionQdrantClient(), collection_prefix="fitfabrica")

    hits = retriever.search(
        query=VectorSearchQuery(
            namespace=VectorNamespace.PRODUCTS,
            embedding=[0.1, 0.2, 0.3],
            limit=5,
        )
    )

    assert hits == []
