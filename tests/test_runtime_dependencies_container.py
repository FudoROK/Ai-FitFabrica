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
    )


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


def test_business_catalog_service_is_cached_and_uses_in_memory_fallback(monkeypatch):
    settings = _settings(environment="test")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage=SimpleNamespace()),
    )

    first = deps.business_catalog_service(settings)
    second = deps.business_catalog_service(settings)

    assert first is second
    assert first.__class__.__name__ == "BusinessCatalogService"


def test_business_catalog_service_prefers_sql_when_available(monkeypatch):
    settings = _settings(environment="prod")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage=SimpleNamespace()),
    )

    service = deps.business_catalog_service(settings)

    assert service._repository.__class__.__name__ == "SqlBusinessCatalogRepository"


def test_provider_runtime_is_cached_per_settings_instance(monkeypatch):
    settings = _settings(environment="prod")
    calls = []

    def _build_provider_runtime(target_settings, *, object_storage):
        calls.append(target_settings)
        assert object_storage == "object-storage"
        return object()

    monkeypatch.setattr(deps, "build_provider_runtime", _build_provider_runtime)
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(object_storage="object-storage"),
    )

    first = deps.provider_runtime(settings)
    second = deps.provider_runtime(settings)

    assert first is second
    assert calls == [settings]
