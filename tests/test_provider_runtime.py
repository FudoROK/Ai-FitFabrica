from __future__ import annotations

from dataclasses import dataclass

from src.llm.provider_runtime import ProviderRuntime, build_provider_runtime


@dataclass
class _LLM:
    provider: str
    vertex_project: str | None = None
    vertex_location: str | None = "us-central1"
    model: str = "test-model"
    vertex_agent_resource: str | None = None
    vertex_memory_daily_agent_resource: str | None = None
    vertex_memory_rolling_agent_resource: str | None = None


@dataclass
class _Settings:
    llm: _LLM


def test_provider_runtime_exposes_structured_reasoning_and_agent_runtime_ports() -> None:
    runtime = ProviderRuntime(
        structured_reasoning=object(),
        agent_runtime=object(),
        embedding_provider=object(),
        image_generation=object(),
        image_editing=object(),
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is not None


def test_registry_builds_structured_reasoning_provider_for_gemini() -> None:
    runtime = build_provider_runtime(
        _Settings(
            llm=_LLM(
                provider="gemini_structured",
                vertex_project="project-id",
            )
        )
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is None


def test_registry_builds_agent_runtime_provider_for_vertex() -> None:
    runtime = build_provider_runtime(
        _Settings(
            llm=_LLM(
                provider="vertex",
                vertex_project="project-id",
                vertex_agent_resource="projects/p/locations/us-central1/reasoningEngines/1",
            )
        )
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is not None
