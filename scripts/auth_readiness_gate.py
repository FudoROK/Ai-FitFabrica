"""Production auth readiness gate for pre-billing preparation."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ARTIFACTS = {
    "backend_auth_routes": "src/entrypoints/public_request_routes.py",
    "backend_auth_route_tests": "tests/test_public_request_routes.py",
    "frontend_sign_in_form": "apps/web/src/features/public/sign-in-form.tsx",
    "frontend_api_client": "apps/web/src/lib/api/client.ts",
    "frontend_api_contracts": "apps/web/src/lib/api/contracts.ts",
    "pre_billing_client_acceptance": "docs/runbooks/pre_billing_client_acceptance_checklist.md",
}

REQUIRED_ENV_KEYS = {
    ".env.example": ("AUTH_PROVIDER", "AUTH_SESSION_COOKIE_NAME"),
    ".env.portable-staging.example": ("AUTH_PROVIDER", "AUTH_SESSION_COOKIE_NAME"),
    ".env.portable-remote-staging.example": ("AUTH_PROVIDER", "AUTH_SESSION_COOKIE_NAME"),
}


def run_gate() -> dict[str, object]:
    """Return auth readiness checks that can run before production auth is connected."""

    checks: dict[str, dict[str, object]] = {}
    failed: list[str] = []
    for name, relative_path in REQUIRED_ARTIFACTS.items():
        path = PROJECT_ROOT / relative_path
        checks[name] = {"status": "passed" if path.exists() else "failed", "path": relative_path}
        if checks[name]["status"] == "failed":
            failed.append(name)
    for name, result in _env_contract_checks().items():
        checks[name] = result
        if result["status"] == "failed":
            failed.append(name)
    for name, result in _source_contract_checks().items():
        checks[name] = result
        if result["status"] == "failed":
            failed.append(name)
    return {
        "gate": "auth_readiness",
        "readiness_status": "blocked" if failed else "ready",
        "failed_checks": failed,
        "checks": checks,
        "external_blockers": ["production_auth_provider_activation"],
        "expected_pre_billing_behavior": {
            "auth_provider": "disabled",
            "sign_in": "503 auth_not_configured",
            "session": "authenticated=false auth_configured=false",
            "logout": "idempotent clears fitfabrica_session",
        },
    }


def _env_contract_checks() -> dict[str, dict[str, object]]:
    """Check that env examples document the auth activation contract."""

    checks: dict[str, dict[str, object]] = {}
    for relative_path, keys in REQUIRED_ENV_KEYS.items():
        path = PROJECT_ROOT / relative_path
        source = path.read_text(encoding="utf-8") if path.exists() else ""
        missing = [key for key in keys if key not in source]
        checks[f"env_{relative_path}"] = {
            "status": "failed" if missing else "passed",
            "path": relative_path,
            "missing": missing,
        }
    return checks


def _source_contract_checks() -> dict[str, dict[str, object]]:
    """Check that current code is fail-closed rather than fake-auth enabled."""

    route_source = (PROJECT_ROOT / "src/entrypoints/public_request_routes.py").read_text(encoding="utf-8")
    domain_source = (PROJECT_ROOT / "src/domain/public_requests.py").read_text(encoding="utf-8")
    frontend_source = (PROJECT_ROOT / "apps/web/src/features/public/sign-in-form.tsx").read_text(encoding="utf-8")
    return {
        "backend_sign_in_fails_closed": {
            "status": "passed" if "status_code=503" in route_source and "auth_not_configured" in domain_source else "failed",
        },
        "frontend_checks_session_before_sign_in": {
            "status": "passed" if "getAuthSession" in frontend_source and "auth_configured" in frontend_source else "failed",
        },
        "frontend_has_no_fake_oauth": {
            "status": "passed" if "Google OAuth" in frontend_source and "window.location" not in frontend_source else "failed",
        },
    }


def main() -> int:
    """CLI entrypoint."""

    report = run_gate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
