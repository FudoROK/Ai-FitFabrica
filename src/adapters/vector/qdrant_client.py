"""Qdrant client bootstrap helpers."""

from __future__ import annotations

import importlib


def build_qdrant_client(settings):
    """Build the shared Qdrant client from validated settings."""
    if not settings.qdrant_url:
        raise ValueError("qdrant_url is required to build the Qdrant client")
    try:
        qdrant_client = importlib.import_module("qdrant_client")
    except ModuleNotFoundError as exc:
        raise RuntimeError("qdrant_client is required when vector infrastructure is configured") from exc
    return qdrant_client.QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=settings.qdrant_request_timeout_seconds,
    )
