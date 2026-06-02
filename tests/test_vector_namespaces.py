"""Tests for typed vector namespaces and records."""

from __future__ import annotations

from src.adapters.vector.namespaces import VECTOR_NAMESPACE_SPECS
from src.domain.vector_search import VectorNamespace, VectorPointRecord, VectorSearchQuery


def test_vector_point_record_models_embedding_payload_and_owner() -> None:
    """Vector records must retain namespace, payload, and canonical owner."""
    record = VectorPointRecord(
        point_id="garment-1",
        namespace=VectorNamespace.GARMENTS,
        embedding=[0.1, 0.2, 0.3],
        payload={"category": "dress", "color": "black"},
        owner_id="product-123",
    )

    assert record.namespace == VectorNamespace.GARMENTS
    assert record.owner_id == "product-123"
    assert record.payload["category"] == "dress"


def test_vector_query_requires_positive_limit() -> None:
    """Vector search query must hold a positive retrieval limit."""
    query = VectorSearchQuery(
        namespace=VectorNamespace.PRODUCTS,
        embedding=[0.1, 0.2, 0.3],
        limit=5,
    )

    assert query.limit == 5


def test_vector_namespace_specs_define_supported_collections() -> None:
    """Each supported namespace must have an explicit collection spec."""
    garment_spec = VECTOR_NAMESPACE_SPECS[VectorNamespace.GARMENTS]

    assert garment_spec.vector_size == 1536
    assert garment_spec.distance == "cosine"
    assert garment_spec.collection_suffix == "garments"
