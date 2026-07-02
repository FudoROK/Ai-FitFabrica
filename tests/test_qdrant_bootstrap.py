from __future__ import annotations

from src.adapters.vector.qdrant_bootstrapper import QdrantVectorBootstrapper
from src.adapters.vector.qdrant_index import collection_name_for_namespace
from src.domain.vector_search import VectorNamespace


class FakeQdrantClient:
    """Local fake Qdrant client for bootstrap behavior tests."""

    def __init__(self, *, collection_exists: bool = False) -> None:
        self._collection_exists = collection_exists
        self.calls: list[tuple[str, object]] = []

    def collection_exists(self, collection_name: str) -> bool:
        self.calls.append(("exists", collection_name))
        return self._collection_exists

    def create_collection(self, **kwargs: object) -> None:
        self.calls.append(("create", kwargs))


def test_collection_name_for_namespace_uses_prefix() -> None:
    name = collection_name_for_namespace(prefix="fitfabrica", namespace="garments")

    assert name == "fitfabrica_garments"


def test_bootstrapper_creates_missing_namespace_collection() -> None:
    """Bootstrapper must create a collection when the namespace is missing."""
    client = FakeQdrantClient(collection_exists=False)
    bootstrapper = QdrantVectorBootstrapper(client=client, collection_prefix="fitfabrica")

    bootstrapper.ensure_collection(namespace=VectorNamespace.GARMENTS)

    assert client.calls[0] == ("exists", "fitfabrica_garments")
    assert client.calls[1][0] == "create"
    assert client.calls[1][1]["vectors_config"]["distance"] == "Cosine"


def test_bootstrapper_skips_create_when_collection_already_exists() -> None:
    """Bootstrapper must not recreate a collection that already exists."""
    client = FakeQdrantClient(collection_exists=True)
    bootstrapper = QdrantVectorBootstrapper(client=client, collection_prefix="fitfabrica")

    bootstrapper.ensure_collection(namespace=VectorNamespace.PRODUCTS)

    assert client.calls == [("exists", "fitfabrica_products")]
