from __future__ import annotations

from types import SimpleNamespace

from src.use_cases.try_on.activation_probe import probe_try_on_real_activation


def test_probe_reports_inactive_when_real_path_is_not_requested() -> None:
    result = probe_try_on_real_activation(
        SimpleNamespace(
            try_on_generation_backend="sandbox_fake",
            enable_real_try_on_generation=False,
            try_on_vertex_failure_fallback_backend="none",
        )
    )

    assert result.readiness_status == "inactive"
    assert result.checks[0].status == "inactive"


def test_probe_reports_ready_for_valid_non_production_activation(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.use_cases.try_on.activation_probe.importlib.util.find_spec",
        lambda _name: object(),
    )
    result = probe_try_on_real_activation(
        SimpleNamespace(
            environment="test",
            try_on_generation_backend="vertex_virtual_try_on",
            enable_real_try_on_generation=True,
            try_on_vertex_failure_fallback_backend="none",
            object_storage_backend="s3",
            object_storage_access_key_id="GOOG1234567890EXAMPLE",
            object_storage_secret_access_key="secret-value-for-staging-hmac",
            postgres_dsn="postgresql+asyncpg://fitfabrica:fitfabrica@localhost:5432/fitfabrica",
            operations_queue_backend="redis",
            redis_url="redis://localhost:6379/0",
            vertex_project="fitfabrica-test",
            vertex_virtual_try_on_model="virtual-try-on-001",
            allow_unsafe_try_on_vertex_fallback_in_production=False,
        )
    )

    assert result.readiness_status == "ready"
    assert all(check.status == "passed" for check in result.checks)


def test_probe_blocks_invalid_production_fallback_policy(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.use_cases.try_on.activation_probe.importlib.util.find_spec",
        lambda _name: object(),
    )
    result = probe_try_on_real_activation(
        SimpleNamespace(
            environment="production",
            try_on_generation_backend="vertex_virtual_try_on",
            enable_real_try_on_generation=True,
            try_on_vertex_failure_fallback_backend="provider_runtime",
            object_storage_backend="s3",
            postgres_dsn="postgresql+asyncpg://fitfabrica:fitfabrica@localhost:5432/fitfabrica",
            operations_queue_backend="redis",
            redis_url="redis://localhost:6379/0",
            vertex_project="fitfabrica-test",
            vertex_virtual_try_on_model="virtual-try-on-001",
            allow_unsafe_try_on_vertex_fallback_in_production=False,
        )
    )

    assert result.readiness_status == "blocked"
    assert any(check.name == "fallback_policy" and check.status == "failed" for check in result.checks)


def test_probe_rejects_placeholder_credentials_and_runtime_values(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.use_cases.try_on.activation_probe.importlib.util.find_spec",
        lambda _name: object(),
    )
    result = probe_try_on_real_activation(
        SimpleNamespace(
            environment="test",
            try_on_generation_backend="vertex_virtual_try_on",
            enable_real_try_on_generation=True,
            try_on_vertex_failure_fallback_backend="none",
            object_storage_backend="s3",
            object_storage_access_key_id="TBD_FROM_GCP_HMAC_ACCESS_ID",
            object_storage_secret_access_key="TBD_FROM_GCP_HMAC_SECRET",
            postgres_dsn="TBD_FROM_GCP_CLOUD_SQL_DSN",
            operations_queue_backend="redis",
            redis_url="TBD_FROM_GCP_REDIS_URL",
            vertex_project="ai-fitfabrica",
            vertex_virtual_try_on_model="virtual-try-on-001",
            allow_unsafe_try_on_vertex_fallback_in_production=False,
        )
    )

    assert result.readiness_status == "blocked"
    assert any(check.name == "object_storage_access_key_id" and check.status == "failed" for check in result.checks)
    assert any(check.name == "object_storage_secret_access_key" and check.status == "failed" for check in result.checks)
    assert any(check.name == "postgres_dsn" and check.status == "failed" for check in result.checks)
    assert any(check.name == "redis_url" and check.status == "failed" for check in result.checks)
