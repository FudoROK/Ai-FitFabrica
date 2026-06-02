from __future__ import annotations

from types import SimpleNamespace

from src.llm.llm_service import LLMService
from src.llm.provider_runtime import ProviderRuntime


class _PortStub:
    """Simple marker object used to verify runtime delegation."""


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        llm=SimpleNamespace(
            provider="vertex",
            mode="live",
            model="gemini-2.0-flash",
            vertex_project="vertex-proj",
            vertex_location="us-central1",
            vertex_agent_resource="projects/p/locations/us-central1/reasoningEngines/1",
            vertex_memory_daily_agent_resource="projects/p/locations/us-central1/reasoningEngines/99",
            vertex_memory_rolling_agent_resource="projects/p/locations/us-central1/reasoningEngines/199",
        )
    )


def test_llm_service_uses_provider_runtime_instead_of_constructing_gemini_directly() -> None:
    runtime = ProviderRuntime(
        structured_reasoning=_PortStub(),
        agent_runtime=None,
        embedding_provider=None,
        image_generation=None,
        image_editing=None,
    )
    service = LLMService(provider=object(), mode="live", settings=_settings(), provider_runtime=runtime)

    selected_provider, routing = service._select_provider_for_task("dialog_reply_task")

    assert routing.structured_provider_used is True
    assert selected_provider is runtime.structured_reasoning


def test_llm_service_uses_agent_runtime_for_memory_runtime_tasks() -> None:
    runtime = ProviderRuntime(
        structured_reasoning=None,
        agent_runtime=_PortStub(),
        embedding_provider=None,
        image_generation=None,
        image_editing=None,
        memory_daily_agent_runtime=_PortStub(),
        memory_rolling_agent_runtime=_PortStub(),
    )
    service = LLMService(provider=object(), mode="live", settings=_settings(), provider_runtime=runtime)

    daily_provider, daily_routing = service._select_provider_for_task("memory_daily_sync_task")
    rolling_provider, rolling_routing = service._select_provider_for_task("memory_rolling_sync_task")

    assert daily_routing.path_name == "memory_daily_runtime"
    assert daily_provider is runtime.memory_daily_agent_runtime
    assert rolling_routing.path_name == "memory_rolling_runtime"
    assert rolling_provider is runtime.memory_rolling_agent_runtime
