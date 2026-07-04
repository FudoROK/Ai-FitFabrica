"""Post-billing acceptance gate for controlled staging validation."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ARTIFACTS = {
    "post_billing_plan": "docs/superpowers/plans/2026-07-02-post-billing-testing-readiness-plan.md",
    "post_billing_gate_runbook": "docs/runbooks/post_billing_acceptance_gate.md",
    "plan_b_report": "docs/reports/2026-07-03-plan-b-no-billing-readiness.md",
    "readiness_endpoint_tests": "tests/test_status_routes_health_runtime.py",
    "frontend_readiness_ui": "tests/test_admin_readiness_page.py",
    "frontend_acceptance_guardrails": "tests/test_no_billing_frontend_guardrails.py",
    "route_documentation_guardrail": "tests/test_frontend_route_documentation.py",
    "try_on_real_activation_smoke": "scripts/try_on_real_activation_smoke.py",
    "try_on_http_worker_smoke": "scripts/try_on_http_worker_live_smoke.py",
    "business_catalog_staging_smoke": "scripts/business_catalog_staging_smoke.py",
    "business_catalog_search_readiness": "scripts/business_catalog_search_index_readiness.py",
    "billing_guardrails": "tests/architecture/test_billing_guardrails.py",
}


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Check whether post-billing acceptance can start.")
    parser.add_argument("--api-base-url", help="Optional backend base URL used to probe GET /ready.")
    parser.add_argument("--status-token", help="STATUS_ENDPOINT_TOKEN for GET /ready.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the gate is ready.")
    return parser


def _local_artifact_checks() -> dict[str, dict[str, object]]:
    """Return presence checks for the required post-billing acceptance assets."""

    checks: dict[str, dict[str, object]] = {}
    for name, relative_path in REQUIRED_ARTIFACTS.items():
        path = PROJECT_ROOT / relative_path
        checks[name] = {
            "status": "passed" if path.exists() else "failed",
            "path": relative_path,
        }
    return checks


def _ready_payload_check(payload: dict[str, object]) -> dict[str, object]:
    """Convert a backend /ready payload into one gate check."""

    blockers = payload.get("blockers", [])
    if not isinstance(blockers, list):
        return {"status": "blocked", "reason": "invalid_blockers_shape", "blockers": []}
    normalized_blockers = [str(blocker) for blocker in blockers]
    ok = bool(payload.get("ok")) and not normalized_blockers
    return {
        "status": "passed" if ok else "blocked",
        "blockers": normalized_blockers,
        "services": payload.get("services", {}),
    }


def _ready_endpoint_check(*, api_base_url: str | None, status_token: str | None) -> dict[str, object]:
    """Probe backend /ready when endpoint details are provided."""

    if not api_base_url:
        return {"status": "skipped", "reason": "api_base_url_not_provided"}
    if not status_token:
        return {"status": "blocked", "reason": "status_token_not_provided"}
    request = urllib.request.Request(
        f"{api_base_url.rstrip('/')}/ready",
        headers={"X-Status-Token": status_token},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"status": "blocked", "reason": f"http_{exc.code}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "reason": str(exc)}
    if not isinstance(payload, dict):
        return {"status": "blocked", "reason": "invalid_ready_payload"}
    return _ready_payload_check(payload)


def run_gate(*, api_base_url: str | None, status_token: str | None) -> dict[str, object]:
    """Run local and optional deployed readiness checks."""

    local_checks = _local_artifact_checks()
    missing_artifacts = [name for name, check in local_checks.items() if check["status"] == "failed"]
    local_status = "failed" if missing_artifacts else "passed"
    ready_endpoint = _ready_endpoint_check(api_base_url=api_base_url, status_token=status_token)
    failed = local_status == "failed" or ready_endpoint["status"] == "blocked"
    return {
        "gate": "post_billing_acceptance",
        "readiness_status": "blocked" if failed else "ready",
        "failed_checks": missing_artifacts + (["ready_endpoint"] if ready_endpoint["status"] == "blocked" else []),
        "checks": {
            "local_artifacts": {
                "status": local_status,
                "missing": missing_artifacts,
                "items": local_checks,
            },
            "ready_endpoint": ready_endpoint,
        },
        "next_commands": [
            "python scripts/platform_foundation_smoke.py --require-ready",
            "python scripts/business_catalog_search_index_readiness.py --require-db",
            "python scripts/try_on_real_activation_smoke.py --require-ready",
            "python scripts/business_catalog_staging_smoke.py",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    args = _parser().parse_args(argv)
    report = run_gate(api_base_url=args.api_base_url, status_token=args.status_token)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.require_ready and report["readiness_status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
