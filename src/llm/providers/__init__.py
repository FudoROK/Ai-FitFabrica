from __future__ import annotations

__all__ = ["VertexProvider", "GeminiStructuredProvider", "FakeProvider", "get_provider"]


def __getattr__(name: str):
    """Avoid importing provider implementations until they are explicitly requested."""
    if name == "FakeProvider":
        from .fake_provider import FakeProvider

        return FakeProvider
    if name == "GeminiStructuredProvider":
        from .gemini_structured_provider import GeminiStructuredProvider

        return GeminiStructuredProvider
    if name == "VertexProvider":
        from ..vertex.vertex_provider import VertexProvider

        return VertexProvider
    if name == "get_provider":
        from .registry import get_provider

        return get_provider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
