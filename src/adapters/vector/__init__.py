"""Portable vector infrastructure adapters."""

from .contracts import VectorIndexBootstrapper
from .qdrant_index import collection_name_for_namespace

__all__ = ["VectorIndexBootstrapper", "build_qdrant_client", "collection_name_for_namespace"]


def __getattr__(name: str):
    """Load optional vector adapters lazily to avoid import-time dependency failures."""
    if name == "build_qdrant_client":
        from .qdrant_client import build_qdrant_client

        return build_qdrant_client
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
