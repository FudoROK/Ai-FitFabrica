"""Approved vector namespaces and collection specs."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.vector_search import VectorNamespace


@dataclass(frozen=True)
class VectorNamespaceSpec:
    """One approved vector namespace and its collection settings."""

    namespace: VectorNamespace
    collection_suffix: str
    vector_size: int
    distance: str


VECTOR_NAMESPACE_SPECS: dict[VectorNamespace, VectorNamespaceSpec] = {
    VectorNamespace.GARMENTS: VectorNamespaceSpec(
        namespace=VectorNamespace.GARMENTS,
        collection_suffix="garments",
        vector_size=1536,
        distance="cosine",
    ),
    VectorNamespace.PRODUCTS: VectorNamespaceSpec(
        namespace=VectorNamespace.PRODUCTS,
        collection_suffix="products",
        vector_size=1536,
        distance="cosine",
    ),
    VectorNamespace.PERSONA_STYLE: VectorNamespaceSpec(
        namespace=VectorNamespace.PERSONA_STYLE,
        collection_suffix="persona_style",
        vector_size=1536,
        distance="cosine",
    ),
    VectorNamespace.RECOGNITION: VectorNamespaceSpec(
        namespace=VectorNamespace.RECOGNITION,
        collection_suffix="recognition",
        vector_size=1536,
        distance="cosine",
    ),
}


def namespace_spec(namespace: VectorNamespace) -> VectorNamespaceSpec:
    """Return the approved collection spec for the requested namespace."""
    return VECTOR_NAMESPACE_SPECS[namespace]
