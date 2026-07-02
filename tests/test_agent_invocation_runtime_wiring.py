from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.llm.provider_runtime import ProviderRuntime
from src.llm.providers.fake_provider import FakeProvider


def test_agent_invocation_runtime_is_cached_and_uses_in_memory_audit_in_tests(monkeypatch) -> None:
    settings = SimpleNamespace(environment="test")
    provider = FakeProvider()
    providers = ProviderRuntime(
        structured_reasoning=provider,
        agent_runtime=provider,
        embedding_provider=None,
        image_generation=None,
        image_editing=None,
    )
    monkeypatch.setattr(deps, "provider_runtime", lambda _settings: providers)
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(
            sql_session_factory=None,
            object_storage=InMemoryObjectStorage(),
        ),
    )

    first = deps.agent_invocation_runtime_dependencies(settings)
    second = deps.agent_invocation_runtime_dependencies(settings)

    assert first is second
    assert first.gateway.__class__.__name__ == "AdkAgentGateway"
    assert first.repository.__class__.__name__ == "InMemoryAgentInvocationRepository"
    assert first.invocation_service.__class__.__name__ == "AgentInvocationService"
