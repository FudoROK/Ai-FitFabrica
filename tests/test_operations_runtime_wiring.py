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
        operations_queue_backend="in_memory",
        operations_queue_name="fitfabrica:workflow-queue",
        operations_worker_name="portable-worker",
        processing_lease_duration_seconds=300,
        postgres_dsn=None,
        redis_url=None,
    )


def test_operations_runtime_dependencies_select_portable_queue_backend(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, redis_client=None, object_storage=object()),
    )

    runtime = deps.operations_runtime_dependencies(settings)

    assert runtime.dispatch_service is not None
    assert runtime.worker_runtime is not None


def test_operations_runtime_dependencies_are_cached(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, redis_client=None, object_storage=object()),
    )

    first = deps.operations_runtime_dependencies(settings)
    second = deps.operations_runtime_dependencies(settings)

    assert first is second
