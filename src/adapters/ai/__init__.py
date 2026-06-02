"""Provider-neutral AI adapters used by backend runtime wiring."""

from .embedding_fake import FakeEmbeddingProvider
from .image_editing_stub import StubImageEditingProvider
from .image_generation_stub import StubImageGenerationProvider
from .vertex_virtual_try_on_client import VertexVirtualTryOnClient

__all__ = [
    "FakeEmbeddingProvider",
    "StubImageEditingProvider",
    "StubImageGenerationProvider",
    "VertexVirtualTryOnClient",
]
