"""Qdrant collection bootstrap behavior."""

from __future__ import annotations

from src.adapters.vector.namespaces import namespace_spec
from src.adapters.vector.qdrant_index import collection_name_for_vector_namespace
from src.domain.vector_search import VectorNamespace


class QdrantVectorBootstrapper:
    """Ensure approved vector collections exist before retrieval operations run."""

    def __init__(self, *, client: object, collection_prefix: str) -> None:
        """Bind the shared Qdrant client plus collection prefix."""
        self._client = client
        self._collection_prefix = collection_prefix

    def ensure_collection(self, *, namespace: VectorNamespace) -> None:
        """Create the namespace collection only when it does not already exist."""
        spec = namespace_spec(namespace)
        collection_name = collection_name_for_vector_namespace(
            prefix=self._collection_prefix,
            namespace=namespace,
        )
        if self._client.collection_exists(collection_name):
            return
        self._client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "size": spec.vector_size,
                "distance": spec.distance.capitalize(),
            },
        )
