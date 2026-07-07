"""Tests for the post-billing acceptance gate script."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import post_billing_acceptance_gate as gate


def test_required_artifact_checks_cover_post_billing_flows() -> None:
    checks = gate._local_artifact_checks()

    assert checks["post_billing_plan"]["status"] == "passed"
    assert checks["pre_billing_client_acceptance_checklist"]["status"] == "passed"
    assert checks["post_billing_live_acceptance_template"]["status"] == "passed"
    assert checks["auth_readiness_gate"]["status"] == "passed"
    assert checks["auth_readiness_runbook"]["status"] == "passed"
    assert checks["billing_readiness_gate"]["status"] == "passed"
    assert checks["billing_readiness_runbook"]["status"] == "passed"
    assert checks["production_infrastructure_readiness_gate"]["status"] == "passed"
    assert checks["production_infrastructure_readiness_runbook"]["status"] == "passed"
    assert checks["production_fallback_usage_audit"]["status"] == "passed"
    assert checks["production_fallback_usage_runbook"]["status"] == "passed"
    assert checks["web_dependency_audit"]["status"] == "passed"
    assert checks["web_dependency_audit_runbook"]["status"] == "passed"
    assert checks["post_billing_gate_runbook"]["status"] == "passed"
    assert checks["readiness_endpoint_tests"]["status"] == "passed"
    assert checks["frontend_readiness_ui"]["status"] == "passed"
    assert checks["frontend_text_encoding_guardrail"]["status"] == "passed"
    assert checks["try_on_real_activation_smoke"]["status"] == "passed"
    assert checks["business_catalog_staging_smoke"]["status"] == "passed"
    assert checks["billing_guardrails"]["status"] == "passed"


def test_ready_payload_check_blocks_when_backend_reports_blockers() -> None:
    check = gate._ready_payload_check(
        {
            "ok": False,
            "blockers": ["billing_core_not_enabled", "admin_auth_not_configured"],
            "services": {"billing": {"status": "blocked", "detail": "Billing core is disabled."}},
        }
    )

    assert check["status"] == "blocked"
    assert check["blockers"] == ["billing_core_not_enabled", "admin_auth_not_configured"]


def test_ready_payload_check_passes_when_backend_has_no_blockers() -> None:
    check = gate._ready_payload_check({"ok": True, "blockers": [], "services": {}})

    assert check["status"] == "passed"
    assert check["blockers"] == []


def test_post_billing_gate_cli_runs_local_checks_without_network() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/post_billing_acceptance_gate.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["gate"] == "post_billing_acceptance"
    assert report["readiness_status"] == "ready"
    assert report["checks"]["local_artifacts"]["status"] == "passed"
    assert "python scripts/production_infrastructure_readiness_gate.py --require-production" in report["next_commands"]
    assert "python scripts/production_fallback_usage_audit.py --require-ready" in report["next_commands"]
    assert "python scripts/web_dependency_audit.py --require-ready" in report["next_commands"]
