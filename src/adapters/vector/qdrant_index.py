"""Qdrant collection naming helpers."""

from __future__ import annotations

from src.adapters.vector.namespaces import namespace_spec
from src.domain.vector_search import VectorNamespace


def collection_name_for_namespace(*, prefix: str, namespace: str) -> str:
    """Build a deterministic Qdrant collection name for a logical namespace."""
    normalized_prefix = prefix.strip().replace("-", "_")
    normalized_namespace = namespace.strip().replace("-", "_")
    return f"{normalized_prefix}_{normalized_namespace}"


def collection_name_for_vector_namespace(*, prefix: str, namespace: VectorNamespace) -> str:
    """Build the deterministic collection name for an approved vector namespace."""
    spec = namespace_spec(namespace)
    return collection_name_for_namespace(prefix=prefix, namespace=spec.collection_suffix)
