"""Provider-neutral AI adapters used by backend runtime wiring."""

from .embedding_fake import FakeEmbeddingProvider
from .image_editing_stub import StubImageEditingProvider
from .image_generation_stub import StubImageGenerationProvider

__all__ = [
    "FakeEmbeddingProvider",
    "StubImageEditingProvider",
    "StubImageGenerationProvider",
]
