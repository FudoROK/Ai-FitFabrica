from dataclasses import dataclass
from typing import Optional

from src.llm.providers.fake_provider import FakeProvider
from src.llm.providers.gemini_structured_provider import GeminiStructuredProvider
from src.llm.providers.registry import get_provider
from src.llm.vertex.vertex_provider import VertexProvider


@dataclass
class _LLM:
    provider: str
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    model: str = "test-model"
    vertex_agent_resource: Optional[str] = None


@dataclass
class _Settings:
    llm: _LLM


def test_registry_returns_vertex_provider():
    provider = get_provider(_Settings(llm=_LLM(provider="vertex", vertex_project="p", vertex_location="us-central1")))
    assert isinstance(provider, VertexProvider)


def test_registry_returns_fake_provider():
    provider = get_provider(_Settings(llm=_LLM(provider="fake")))
    assert isinstance(provider, FakeProvider)


def test_registry_returns_gemini_structured_provider():
    provider = get_provider(_Settings(llm=_LLM(provider="gemini_structured", vertex_project="p", vertex_location="us-central1")))
    assert isinstance(provider, GeminiStructuredProvider)
