"""Backend-owned provider runtime composition and selection."""

from __future__ import annotations

from dataclasses import dataclass

from src.adapters.ai import FakeEmbeddingProvider, StubImageEditingProvider, StubImageGenerationProvider
from src.domain.provider_ports import (
    AgentRuntimePort,
    EmbeddingProviderPort,
    ImageEditingPort,
    ImageGenerationPort,
    StructuredReasoningPort,
)
from src.llm.providers.fake_provider import FakeProvider
from src.llm.providers.gemini_structured_provider import GeminiStructuredProvider
from src.llm.vertex.vertex_provider import VertexProvider


@dataclass(frozen=True)
class ProviderRuntime:
    """Composed provider runtime owned by backend wiring."""

    structured_reasoning: StructuredReasoningPort | None
    agent_runtime: AgentRuntimePort | None
    embedding_provider: EmbeddingProviderPort | None
    image_generation: ImageGenerationPort | None
    image_editing: ImageEditingPort | None
    memory_daily_agent_runtime: AgentRuntimePort | None = None
    memory_rolling_agent_runtime: AgentRuntimePort | None = None


def build_provider_runtime(settings) -> ProviderRuntime:
    """Build provider runtime adapters from settings without leaking selection into business code."""
    provider_name = (settings.llm.provider or "").strip().lower()
    embedding_provider = FakeEmbeddingProvider()
    image_generation = StubImageGenerationProvider()
    image_editing = StubImageEditingProvider()

    if provider_name == "fake":
        fake_provider = FakeProvider()
        return ProviderRuntime(
            structured_reasoning=fake_provider,
            agent_runtime=fake_provider,
            embedding_provider=embedding_provider,
            image_generation=image_generation,
            image_editing=image_editing,
            memory_daily_agent_runtime=fake_provider,
            memory_rolling_agent_runtime=fake_provider,
        )

    if provider_name == "gemini_structured":
        return ProviderRuntime(
            structured_reasoning=GeminiStructuredProvider(settings=settings),
            agent_runtime=None,
            embedding_provider=embedding_provider,
            image_generation=image_generation,
            image_editing=image_editing,
        )

    if provider_name == "vertex":
        memory_daily_resource = (settings.llm.vertex_memory_daily_agent_resource or "").strip()
        memory_rolling_resource = (settings.llm.vertex_memory_rolling_agent_resource or "").strip()
        return ProviderRuntime(
            structured_reasoning=GeminiStructuredProvider(settings=settings),
            agent_runtime=VertexProvider(settings=settings),
            embedding_provider=embedding_provider,
            image_generation=image_generation,
            image_editing=image_editing,
            memory_daily_agent_runtime=(
                VertexProvider(settings=settings, agent_resource_override=memory_daily_resource)
                if memory_daily_resource
                else None
            ),
            memory_rolling_agent_runtime=(
                VertexProvider(settings=settings, agent_resource_override=memory_rolling_resource)
                if memory_rolling_resource
                else None
            ),
        )

    raise ValueError(f"Unsupported provider runtime: {provider_name}")
