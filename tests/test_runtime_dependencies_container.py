from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps
from src.memory_layer.run_ledger_repository import (
    FirestoreMemoryRunLedgerRepository,
    InMemoryMemoryRunLedgerRepository,
)


class _DummyLimiter:
    pass


def _settings(environment: str = "prod"):
    return SimpleNamespace(
        environment=environment,
        ingress_rate_limit_max_events=20,
        ingress_rate_limit_window_seconds=60,
        ingress_rate_limit_collection="ingress_rate_limits",
        ingress_global_safety_cap_max_events=2000,
    )


def test_runtime_container_reuses_dialog_and_memory_services(monkeypatch):
    settings = _settings()

    dialog_instances = []
    memory_instances = []

    class _DialogServiceStub:
        def __init__(self, **kwargs):
            dialog_instances.append(kwargs)

    class _MemorySummaryServiceStub:
        def __init__(self, **kwargs):
            memory_instances.append(kwargs)

    monkeypatch.setattr(deps, "DialogService", _DialogServiceStub)
    monkeypatch.setattr(deps, "MemorySummaryService", _MemorySummaryServiceStub)
    monkeypatch.setattr(deps, "get_messaging_adapter", lambda: "messaging")
    monkeypatch.setattr(deps, "FirestoreLeadRepository", lambda **kwargs: {"repo": "lead_repo", "kwargs": kwargs})
    monkeypatch.setattr(deps, "FirestoreSessionRepository", lambda: "session_repo")
    monkeypatch.setattr(deps, "get_firestore_client", lambda: "firestore")
    monkeypatch.setattr(deps, "create_rate_limiter", lambda *_args, **_kwargs: "dialog_rate_limiter")

    first_dialog = deps.dialog_service(settings)
    second_dialog = deps.dialog_service(settings)
    first_memory = deps.memory_summary_service(settings)
    second_memory = deps.memory_summary_service(settings)

    assert first_dialog is second_dialog
    assert first_memory is second_memory
    assert len(dialog_instances) == 1
    assert len(memory_instances) == 1
    assert "memory_layer_service" in dialog_instances[0]["leads_repo"]["kwargs"]
    assert "memory_layer_service" in memory_instances[0]["leads_repo"]["kwargs"]
    assert isinstance(
        memory_instances[0]["memory_run_ledger_service"].repository,
        FirestoreMemoryRunLedgerRepository,
    )


def test_runtime_container_uses_inmemory_memory_run_ledger_service_in_test_env(monkeypatch):
    settings = _settings(environment="test")
    memory_instances = []

    class _MemorySummaryServiceStub:
        def __init__(self, **kwargs):
            memory_instances.append(kwargs)

    monkeypatch.setattr(deps, "MemorySummaryService", _MemorySummaryServiceStub)
    monkeypatch.setattr(deps, "FirestoreLeadRepository", lambda **kwargs: {"repo": "lead_repo", "kwargs": kwargs})
    monkeypatch.setattr(deps, "get_firestore_client", lambda: None)

    deps.memory_summary_service(settings)

    assert len(memory_instances) == 1
    assert isinstance(
        memory_instances[0]["memory_run_ledger_service"].repository,
        InMemoryMemoryRunLedgerRepository,
    )


def test_runtime_container_reuses_non_test_ingress_limiters(monkeypatch):
    settings = _settings(environment="prod")
    calls = []

    def _limiter_factory(_settings, **kwargs):
        calls.append(kwargs)
        return _DummyLimiter()

    monkeypatch.setattr(deps, "create_rate_limiter", _limiter_factory)

    limiter_a = deps.ingress_rate_limiter(settings)
    limiter_b = deps.ingress_rate_limiter(settings)
    global_limiter_a = deps.ingress_global_safety_limiter(settings)
    global_limiter_b = deps.ingress_global_safety_limiter(settings)

    assert limiter_a is limiter_b
    assert global_limiter_a is global_limiter_b
    assert len(calls) == 2


def test_runtime_container_uses_inmemory_ingress_limiters_in_test_env(monkeypatch):
    settings = _settings(environment="test")
    calls = []

    def _limiter_factory(_settings, **kwargs):
        calls.append(kwargs)
        return _DummyLimiter()

    monkeypatch.setattr(deps, "create_rate_limiter", _limiter_factory)

    limiter_a = deps.ingress_rate_limiter(settings)
    limiter_b = deps.ingress_rate_limiter(settings)
    global_limiter_a = deps.ingress_global_safety_limiter(settings)
    global_limiter_b = deps.ingress_global_safety_limiter(settings)

    assert limiter_a is not limiter_b
    assert global_limiter_a is not global_limiter_b
    assert all(call.get("backend_override") == "inmemory" for call in calls)


def test_portable_infrastructure_is_cached_per_settings_instance(monkeypatch):
    settings = SimpleNamespace()
    calls = []

    def _build_portable_infrastructure(target_settings):
        calls.append(target_settings)
        return object()

    monkeypatch.setattr(deps, "build_portable_infrastructure", _build_portable_infrastructure)

    first = deps.portable_infrastructure(settings)
    second = deps.portable_infrastructure(settings)

    assert first is second
    assert calls == [settings]


def test_runtime_identity_repositories_prefer_sql_when_portable_infrastructure_exists(monkeypatch):
    settings = _settings(environment="prod")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory"),
    )

    repositories = deps.identity_runtime_repositories(settings)

    assert repositories.channel_identity_repo.__class__.__name__.startswith("Sql")


def test_identity_audit_recorder_prefers_sql_when_portable_infrastructure_exists(monkeypatch):
    settings = _settings(environment="prod")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory"),
    )

    recorder = deps.identity_audit_recorder(settings)

    assert recorder.__class__.__name__ == "SqlIdentityResolutionAuditRecorder"


def test_provider_runtime_is_cached_per_settings_instance(monkeypatch):
    settings = _settings(environment="prod")
    calls = []

    def _build_provider_runtime(target_settings):
        calls.append(target_settings)
        return object()

    monkeypatch.setattr(deps, "build_provider_runtime", _build_provider_runtime)

    first = deps.provider_runtime(settings)
    second = deps.provider_runtime(settings)

    assert first is second
    assert calls == [settings]
