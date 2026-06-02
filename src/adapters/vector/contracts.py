"""Vector infrastructure contracts."""

from __future__ import annotations

from typing import Protocol

from src.domain.vector_search import VectorPointRecord, VectorSearchHit, VectorSearchQuery


class VectorIndexBootstrapper(Protocol):
    """Bootstrap contract for vector index namespaces."""

    def ensure_collection(self, *, namespace: str, vector_size: int) -> None:
        """Ensure the named collection exists with the expected vector size."""


class VectorRetriever(Protocol):
    """Retrieval contract for vector-backed similarity search."""

    def upsert_points(self, *, records: list[VectorPointRecord]) -> None:
        """Persist or replace vector records in the backing index."""

    def search(self, *, query: VectorSearchQuery) -> list[VectorSearchHit]:
        """Run a similarity search and return typed hit payloads."""
