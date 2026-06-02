from __future__ import annotations

from src.adapters.ai.embedding_fake import FakeEmbeddingProvider
from src.domain.provider_models import EmbeddingRequest


def test_fake_embedding_provider_returns_stable_embedding_shape() -> None:
    provider = FakeEmbeddingProvider(vector_size=4)

    result = provider.embed(
        EmbeddingRequest(
            namespace="garments",
            input_text="black dress with belt",
        )
    )

    assert result.namespace == "garments"
    assert len(result.embedding) == 4
    assert result.provider == "fake_embedding"
