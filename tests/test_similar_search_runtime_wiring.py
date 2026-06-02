from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        environment="prod",
        object_storage_prefix="fitfabrica",
        ingress_rate_limit_max_events=20,
        ingress_rate_limit_window_seconds=60,
        ingress_rate_limit_collection="ingress_rate_limits",
        ingress_global_safety_cap_max_events=2000,
    )


def test_similar_search_runtime_dependencies_use_qdrant_and_sql_catalog(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", qdrant_client=object(), object_storage=object()),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(embedding_provider=object()),
    )

    runtime = deps.similar_search_runtime_dependencies(settings)

    assert runtime.workflow_service is not None

