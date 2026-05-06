from __future__ import annotations

from .base import LLMProvider
from .fake_provider import FakeProvider
from .gemini_structured_provider import GeminiStructuredProvider
from ..vertex.vertex_provider import VertexProvider


def get_provider(settings, **kwargs) -> LLMProvider:
    provider_name = (settings.llm.provider or "").strip().lower()
    if provider_name == "fake":
        return FakeProvider(**kwargs)
    if provider_name == "vertex":
        return VertexProvider(settings=settings, **kwargs)
    if provider_name == "gemini_structured":
        return GeminiStructuredProvider(settings=settings, **kwargs)
    raise ValueError(f"Unsupported LLM provider: {provider_name}")
