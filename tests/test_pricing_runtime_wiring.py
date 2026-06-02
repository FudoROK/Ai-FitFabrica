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


def test_pricing_runtime_dependencies_wire_repository_and_comparison_source(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage=object()),
    )

    runtime = deps.pricing_runtime_dependencies(settings)

    assert runtime.workflow_service is not None


def test_pricing_runtime_dependencies_are_cached(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage=object()),
    )

    first = deps.pricing_runtime_dependencies(settings)
    second = deps.pricing_runtime_dependencies(settings)

    assert first is second
