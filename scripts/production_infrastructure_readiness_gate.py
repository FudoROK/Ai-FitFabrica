"""Production infrastructure readiness gate for post-billing activation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ENVIRONMENTS = frozenset({"prod", "production", "staging", "stage", "live"})

REQUIRED_VALUES = {
    "object_storage_backend": ("OBJECT_STORAGE_BACKEND", "s3"),
    "operations_queue_backend": ("OPERATIONS_QUEUE_BACKEND", "redis"),
    "rate_limit_backend": ("RATE_LIMIT_BACKEND", "redis"),
    "rate_limit_fail_mode": ("RATE_LIMIT_FAIL_MODE", "closed"),
    "billing_core_enabled": ("BILLING_CORE_ENABLED", "true"),
    "llm_provider": ("LLM_PROVIDER", ("vertex", "gemini_structured")),
    "llm_gateway_mode": ("LLM_GATEWAY_MODE", ("live", "provider_runtime", "production")),
    "image_editing_provider": ("IMAGE_EDITING_PROVIDER", "google_genai"),
    "try_on_generation_backend": ("TRY_ON_GENERATION_BACKEND", "vertex_virtual_try_on"),
    "enable_real_try_on_generation": ("ENABLE_REAL_TRY_ON_GENERATION", "true"),
    "try_on_vertex_failure_fallback_backend": ("TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND", "none"),
    "allow_unsafe_try_on_vertex_fallback_in_production": (
        "ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION",
        "false",
    ),
    "allow_unsafe_admin_header_auth": ("ALLOW_UNSAFE_ADMIN_HEADER_AUTH", "false"),
}

REQUIRED_NON_EMPTY = {
    "postgres_dsn": "POSTGRES_DSN",
    "redis_url": "REDIS_URL",
    "object_storage_bucket_name": "OBJECT_STORAGE_BUCKET_NAME",
    "object_storage_access_key_id": "OBJECT_STORAGE_ACCESS_KEY_ID",
    "object_storage_secret_access_key": "OBJECT_STORAGE_SECRET_ACCESS_KEY",
    "auth_provider": "AUTH_PROVIDER",
    "vertex_project": "VERTEX_PROJECT",
    "vertex_location": "VERTEX_LOCATION",
    "vertex_virtual_try_on_location": "VERTEX_VIRTUAL_TRY_ON_LOCATION",
    "vertex_virtual_try_on_model": "VERTEX_VIRTUAL_TRY_ON_MODEL",
    "vertex_agent_resource": "VERTEX_AGENT_RESOURCE",
    "status_endpoint_token": "STATUS_ENDPOINT_TOKEN",
    "admin_api_token": "ADMIN_API_TOKEN",
}

DISALLOWED_VALUES = {
    "auth_provider": ("disabled", "none", "stub", "fake"),
    "postgres_dsn": ("", "placeholder", "replace-with-password"),
    "redis_url": ("", "placeholder"),
    "status_endpoint_token": ("", "placeholder", "replace-with-staging-status-token", "your-health-check-api-key"),
    "admin_api_token": ("", "placeholder", "replace-with-internal-admin-token", "your-internal-admin-api-token"),
    "vertex_project": ("", "placeholder", "your-vertex-project-id"),
    "vertex_agent_resource": ("", "placeholder", "replace-with", "your-"),
    "object_storage_access_key_id": ("", "placeholder", "replace-with", "your-"),
    "object_storage_secret_access_key": ("", "placeholder", "replace-with", "your-"),
}


def run_gate(*, env: dict[str, str] | None = None, require_production: bool = False) -> dict[str, object]:
    """Return production infrastructure readiness checks."""

    values = {key: str(value) for key, value in (env or os.environ).items()}
    environment = _normalized(_get(values, "ENVIRONMENT", "APP_ENV", "ENV") or "local")
    production_scope = require_production or environment in PRODUCTION_ENVIRONMENTS
    checks: dict[str, dict[str, object]] = {
        "production_scope": {
            "status": "passed" if production_scope else "skipped",
            "environment": environment,
            "require_production": require_production,
        }
    }
    failed: list[str] = []
    if not production_scope:
        return _report(checks=checks, failed=failed)

    for name, env_key in REQUIRED_NON_EMPTY.items():
        value = _get(values, env_key)
        result = _non_empty_check(name=name, env_key=env_key, value=value)
        checks[name] = result
        if result["status"] == "failed":
            failed.append(name)
    for name, (env_key, expected) in REQUIRED_VALUES.items():
        value = _get(values, env_key)
        result = _expected_value_check(env_key=env_key, value=value, expected=expected)
        checks[name] = result
        if result["status"] == "failed":
            failed.append(name)
    for name, disallowed in DISALLOWED_VALUES.items():
        if name not in checks:
            continue
        value = _normalized(str(checks[name].get("value", "")))
        if any(_is_disallowed_value(value=value, marker=marker) for marker in disallowed):
            checks[name] = {**checks[name], "status": "failed", "reason": "placeholder_or_disabled_value"}
            if name not in failed:
                failed.append(name)
    return _report(checks=checks, failed=failed)


def _report(*, checks: dict[str, dict[str, object]], failed: list[str]) -> dict[str, object]:
    return {
        "gate": "production_infrastructure_readiness",
        "readiness_status": "blocked" if failed else "ready",
        "failed_checks": failed,
        "checks": checks,
        "post_billing_expectation": {
            "persistence": "postgresql",
            "object_storage": "s3",
            "queue": "redis",
            "auth": "enabled",
            "billing": "enabled",
            "ai_provider": "live",
            "try_on_generation": "vertex_virtual_try_on",
            "unsafe_fallbacks": "disabled",
        },
    }


def _non_empty_check(*, name: str, env_key: str, value: str | None) -> dict[str, object]:
    normalized = _normalized(value)
    if name == "auth_provider" and normalized in {"disabled", "none", "stub", "fake"}:
        return {"status": "failed", "env_key": env_key, "value": value or "", "reason": "auth_provider_disabled"}
    if _contains_placeholder(normalized):
        return {"status": "failed", "env_key": env_key, "value": value or "", "reason": "placeholder_value"}
    return {
        "status": "passed" if normalized else "failed",
        "env_key": env_key,
        "value": value or "",
    }


def _expected_value_check(*, env_key: str, value: str | None, expected: str | tuple[str, ...]) -> dict[str, object]:
    normalized = _normalized(value)
    if isinstance(expected, tuple):
        ok = normalized in expected
        expected_value: object = list(expected)
    else:
        ok = normalized == expected
        expected_value = expected
    return {
        "status": "passed" if ok else "failed",
        "env_key": env_key,
        "expected": expected_value,
        "value": value or "",
    }


def _get(values: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        if key in values:
            return values[key]
    return None


def _normalized(value: object | None) -> str:
    return str(value or "").strip().lower()


def _is_disallowed_value(*, value: str, marker: str) -> bool:
    if marker == "":
        return value == ""
    return marker in value


def _contains_placeholder(value: str) -> bool:
    return any(marker in value for marker in ("replace-with", "placeholder", "your-"))


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check production infrastructure readiness.")
    parser.add_argument("--env-file", help="Optional env file to check instead of process environment.")
    parser.add_argument("--require-production", action="store_true", help="Run production checks even for local env.")
    return parser


def main() -> int:
    args = _parser().parse_args()
    env = _parse_env_file(PROJECT_ROOT / args.env_file) if args.env_file else None
    report = run_gate(env=env, require_production=args.require_production)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
