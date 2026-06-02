"""Deterministic fake embedding adapter for tests and local wiring."""

from __future__ import annotations

from hashlib import sha256

from src.domain.provider_models import EmbeddingRequest, EmbeddingResult


class FakeEmbeddingProvider:
    """Return deterministic embeddings without calling an external provider."""

    provider_name = "fake_embedding"

    def __init__(self, *, vector_size: int = 8, model_name: str = "fake-embedding-v1") -> None:
        self.vector_size = vector_size
        self.model_name = model_name

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Build a stable numeric vector from the request text."""
        digest = sha256(f"{request.namespace}:{request.input_text}".encode("utf-8")).digest()
        embedding = [
            round(int(digest[index % len(digest)]) / 255.0, 6)
            for index in range(self.vector_size)
        ]
        return EmbeddingResult(
            namespace=request.namespace,
            embedding=embedding,
            provider=self.provider_name,
            model=self.model_name,
        )
