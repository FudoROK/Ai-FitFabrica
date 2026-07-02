from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps


def _settings(environment: str = "prod"):
    return SimpleNamespace(
        environment=environment,
        ingress_rate_limit_max_events=20,
        ingress_rate_limit_window_seconds=60,
        ingress_rate_limit_collection="ingress_rate_limits",
        ingress_global_safety_cap_max_events=2000,
        object_storage_prefix="fitfabrica",
    )


def test_product_card_runtime_dependencies_prefer_sql_and_portable_storage(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage=object()),
    )

    runtime = deps.product_card_runtime_dependencies(settings)

    assert runtime.workflow_service is not None
    assert runtime.workflow_service._garment_identity_analyzer._taxonomy_service.__class__.__name__ == "GarmentTaxonomyService"


def test_product_card_runtime_dependencies_are_cached(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage=object()),
    )

    first = deps.product_card_runtime_dependencies(settings)
    second = deps.product_card_runtime_dependencies(settings)

    assert first is second


def test_product_card_runtime_uses_fake_generation_only_in_test(monkeypatch) -> None:
    settings = _settings(environment="test")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage=object()),
    )

    runtime = deps.product_card_runtime_dependencies(settings)

    assert runtime.workflow_service._generation_adapter.__class__.__name__ == "FakeProductCardGenerationAdapter"
    assert runtime.workflow_service._garment_identity_analyzer.__class__.__name__ == "DeterministicGarmentIdentityAnalysisAdapter"


def test_product_card_runtime_uses_agent_generation_outside_test(monkeypatch) -> None:
    settings = _settings(environment="prod")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage=object()),
    )
    monkeypatch.setattr(
        deps,
        "agent_invocation_runtime_dependencies",
        lambda _settings: SimpleNamespace(invocation_service=object()),
    )

    runtime = deps.product_card_runtime_dependencies(settings)

    assert runtime.workflow_service._generation_adapter.__class__.__name__ == "ProductCardAgentGenerationAdapter"
    assert runtime.workflow_service._generation_adapter._preferred_model == "gemini-2.5-flash-lite"
    assert runtime.workflow_service._garment_identity_analyzer.__class__.__name__ == "GarmentIdentityAnalysisAdapter"
    assert runtime.workflow_service._garment_identity_analyzer._preferred_model == "gemini-2.5-flash"
    assert runtime.workflow_service._garment_identity_analyzer._taxonomy_service is None
