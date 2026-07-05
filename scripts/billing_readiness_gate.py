"""Billing activation readiness gate for pre-billing preparation."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ARTIFACTS = {
    "billing_domain": "src/domain/billing.py",
    "billing_service": "src/use_cases/billing/service.py",
    "billing_policy": "src/use_cases/billing/policy.py",
    "billing_ports": "src/use_cases/billing/ports.py",
    "billing_sql_repository": "src/adapters/database/sql/billing_repositories.py",
    "billing_sql_models": "src/adapters/database/sql/billing_models.py",
    "credits_routes": "src/entrypoints/credits_routes.py",
    "workspace_credits_page": "apps/web/src/features/workspace/workspace-credits-view.tsx",
    "billing_guardrails": "tests/architecture/test_billing_guardrails.py",
    "billing_service_tests": "tests/test_billing_service.py",
    "billing_policy_tests": "tests/test_billing_policy.py",
    "billing_sql_repository_tests": "tests/test_billing_sql_repositories.py",
    "credits_route_tests": "tests/test_credits_routes.py",
    "credits_policy_doc": "docs/costs/credits_policy_v1.md",
    "credits_pricing_doc": "docs/costs/credits_pricing_table_v1.md",
}

REQUIRED_ENV_KEYS = {
    ".env.example": ("BILLING_CORE_ENABLED=false",),
    ".env.portable-staging.example": ("BILLING_CORE_ENABLED=false",),
    ".env.portable-remote-staging.example": ("BILLING_CORE_ENABLED=false",),
}


def run_gate() -> dict[str, object]:
    """Return billing readiness checks that are safe before billing activation."""

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
        "gate": "billing_readiness",
        "readiness_status": "blocked" if failed else "ready",
        "failed_checks": failed,
        "checks": checks,
        "external_blockers": ["billing_core_activation", "payment_provider_activation"],
        "expected_pre_billing_behavior": {
            "billing_core_enabled": False,
            "credits_source": "backend_owned_api",
            "frontend_credit_calculation": "display_only",
            "ledger_authority": "backend_sql_repository",
        },
    }


def _env_contract_checks() -> dict[str, dict[str, object]]:
    """Check env examples keep billing disabled until activation."""

    checks: dict[str, dict[str, object]] = {}
    for relative_path, fragments in REQUIRED_ENV_KEYS.items():
        path = PROJECT_ROOT / relative_path
        source = path.read_text(encoding="utf-8") if path.exists() else ""
        missing = [fragment for fragment in fragments if fragment not in source]
        checks[f"env_{relative_path}"] = {
            "status": "failed" if missing else "passed",
            "path": relative_path,
            "missing": missing,
        }
    return checks


def _source_contract_checks() -> dict[str, dict[str, object]]:
    """Check backend authority and frontend display-only billing boundaries."""

    credits_route = (PROJECT_ROOT / "src/entrypoints/credits_routes.py").read_text(encoding="utf-8")
    billing_service = (PROJECT_ROOT / "src/use_cases/billing/service.py").read_text(encoding="utf-8")
    billing_repository = (PROJECT_ROOT / "src/adapters/database/sql/billing_repositories.py").read_text(
        encoding="utf-8"
    )
    frontend_credits = (PROJECT_ROOT / "apps/web/src/features/workspace/workspace-credits-view.tsx").read_text(
        encoding="utf-8"
    )
    return {
        "credits_routes_delegate_to_billing_service": {
            "status": "passed"
            if "billing_runtime_dependencies" in credits_route and "get_account_balance" in credits_route
            else "failed",
        },
        "billing_service_appends_ledger_events": {
            "status": "passed"
            if "append_ledger_event" in billing_service and "idempotency_key" in billing_service
            else "failed",
        },
        "sql_repository_prevents_negative_balance": {
            "status": "passed" if "Credit balance cannot become negative" in billing_repository else "failed",
        },
        "frontend_displays_backend_credit_dtos": {
            "status": "passed"
            if "getCreditBalance" in frontend_credits and "getCreditLedger" in frontend_credits
            else "failed",
        },
        "frontend_does_not_compute_credit_balance": {
            "status": "passed"
            if "available_credits -" not in frontend_credits and "credits_delta =" not in frontend_credits
            else "failed",
        },
    }


def main() -> int:
    """CLI entrypoint."""

    report = run_gate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
