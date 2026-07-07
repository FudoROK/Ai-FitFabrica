"""Tests for the production infrastructure readiness gate."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import production_infrastructure_readiness_gate as gate


def _production_env(**overrides: str) -> dict[str, str]:
    env = {
        "ENVIRONMENT": "production",
        "POSTGRES_DSN": "postgresql+asyncpg://fitfabrica:secret@postgres:5432/fitfabrica",
        "REDIS_URL": "redis://redis:6379/0",
        "OBJECT_STORAGE_BACKEND": "s3",
        "OBJECT_STORAGE_BUCKET_NAME": "fitfabrica-prod-media",
        "OBJECT_STORAGE_ACCESS_KEY_ID": "prod-object-access-key",
        "OBJECT_STORAGE_SECRET_ACCESS_KEY": "prod-object-secret-key",
        "OPERATIONS_QUEUE_BACKEND": "redis",
        "RATE_LIMIT_BACKEND": "redis",
        "RATE_LIMIT_FAIL_MODE": "closed",
        "AUTH_PROVIDER": "firebase",
        "BILLING_CORE_ENABLED": "true",
        "LLM_PROVIDER": "vertex",
        "LLM_GATEWAY_MODE": "live",
        "IMAGE_EDITING_PROVIDER": "google_genai",
        "TRY_ON_GENERATION_BACKEND": "vertex_virtual_try_on",
        "ENABLE_REAL_TRY_ON_GENERATION": "true",
        "TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND": "none",
        "ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION": "false",
        "VERTEX_PROJECT": "fitfabrica-prod",
        "VERTEX_LOCATION": "us-central1",
        "VERTEX_VIRTUAL_TRY_ON_LOCATION": "global",
        "VERTEX_VIRTUAL_TRY_ON_MODEL": "virtual-try-on-001",
        "VERTEX_AGENT_RESOURCE": "projects/fitfabrica-prod/locations/us-central1/reasoningEngines/agent",
        "STATUS_ENDPOINT_TOKEN": "status-token",
        "ADMIN_API_TOKEN": "admin-token",
        "ALLOW_UNSAFE_ADMIN_HEADER_AUTH": "false",
    }
    env.update(overrides)
    return env


def test_production_gate_blocks_missing_durable_infrastructure() -> None:
    """Production-like environments must not use local persistence or queue fallbacks."""
    report = gate.run_gate(
        env=_production_env(
            POSTGRES_DSN="",
            REDIS_URL="",
            OBJECT_STORAGE_BACKEND="in_memory",
            OPERATIONS_QUEUE_BACKEND="in_memory",
        )
    )

    assert report["readiness_status"] == "blocked"
    assert "postgres_dsn" in report["failed_checks"]
    assert "redis_url" in report["failed_checks"]
    assert "object_storage_backend" in report["failed_checks"]
    assert "operations_queue_backend" in report["failed_checks"]


def test_production_gate_blocks_fake_provider_and_sandbox_try_on() -> None:
    """Production-like environments must not silently run on fake AI or sandbox generation."""
    report = gate.run_gate(
        env=_production_env(
            LLM_PROVIDER="fake",
            LLM_GATEWAY_MODE="stub",
            TRY_ON_GENERATION_BACKEND="sandbox_fake",
            ENABLE_REAL_TRY_ON_GENERATION="false",
        )
    )

    assert report["readiness_status"] == "blocked"
    assert "llm_provider" in report["failed_checks"]
    assert "llm_gateway_mode" in report["failed_checks"]
    assert "try_on_generation_backend" in report["failed_checks"]
    assert "enable_real_try_on_generation" in report["failed_checks"]


def test_production_gate_blocks_disabled_auth_billing_and_unsafe_fallbacks() -> None:
    """Production-like environments must have auth/billing on and dangerous fallbacks off."""
    report = gate.run_gate(
        env=_production_env(
            AUTH_PROVIDER="disabled",
            BILLING_CORE_ENABLED="false",
            TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND="sandbox_fake",
            ALLOW_UNSAFE_ADMIN_HEADER_AUTH="true",
        )
    )

    assert report["readiness_status"] == "blocked"
    assert "auth_provider" in report["failed_checks"]
    assert "billing_core_enabled" in report["failed_checks"]
    assert "try_on_vertex_failure_fallback_backend" in report["failed_checks"]
    assert "allow_unsafe_admin_header_auth" in report["failed_checks"]


def test_production_gate_passes_complete_production_contract() -> None:
    """A complete production-like env should be accepted for post-billing live testing."""
    report = gate.run_gate(env=_production_env())

    assert report["gate"] == "production_infrastructure_readiness"
    assert report["readiness_status"] == "ready"
    assert report["failed_checks"] == []


def test_production_gate_skips_local_environment_without_breaking_pre_billing() -> None:
    """Local no-billing runs should not be blocked by production-only checks."""
    report = gate.run_gate(env={"ENVIRONMENT": "local"})

    assert report["readiness_status"] == "ready"
    assert report["checks"]["production_scope"]["status"] == "skipped"


def test_production_gate_cli_prints_machine_readable_report() -> None:
    """Operators should be able to run the gate from the command line."""
    result = subprocess.run(
        [sys.executable, "scripts/production_infrastructure_readiness_gate.py", "--env-file", ".env.example"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["gate"] == "production_infrastructure_readiness"


def test_post_billing_staging_env_template_uses_production_like_modes() -> None:
    """Post-billing staging template should document live-mode runtime values."""
    env = gate._parse_env_file(gate.PROJECT_ROOT / ".env.post-billing-staging.example")

    assert env["AUTH_PROVIDER"] == "firebase"
    assert env["BILLING_CORE_ENABLED"] == "true"
    assert env["LLM_PROVIDER"] == "vertex"
    assert env["LLM_GATEWAY_MODE"] == "live"
    assert env["IMAGE_EDITING_PROVIDER"] == "google_genai"
    assert env["TRY_ON_GENERATION_BACKEND"] == "vertex_virtual_try_on"
    assert env["ENABLE_REAL_TRY_ON_GENERATION"] == "true"
    assert env["TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND"] == "none"
    assert env["ALLOW_UNSAFE_ADMIN_HEADER_AUTH"] == "false"
    assert env["ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION"] == "false"


def test_production_gate_blocks_placeholder_values_in_post_billing_template() -> None:
    """The example file is not deployable until operator placeholders are replaced."""
    env = gate._parse_env_file(gate.PROJECT_ROOT / ".env.post-billing-staging.example")

    report = gate.run_gate(env=env, require_production=True)

    assert report["readiness_status"] == "blocked"
    assert "postgres_dsn" in report["failed_checks"]
    assert "status_endpoint_token" in report["failed_checks"]
    assert "admin_api_token" in report["failed_checks"]
    assert "vertex_agent_resource" in report["failed_checks"]
