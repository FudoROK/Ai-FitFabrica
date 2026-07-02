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

