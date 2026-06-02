"""Tests for the first Qdrant retriever adapter."""

from __future__ import annotations

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
