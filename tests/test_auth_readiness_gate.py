"""Tests for the production auth readiness gate."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import auth_readiness_gate as gate


def test_auth_readiness_gate_reports_safe_pre_billing_state() -> None:
    """The gate must prove auth is fail-closed before production auth is activated."""
    report = gate.run_gate()

    assert report["gate"] == "auth_readiness"
    assert report["readiness_status"] == "ready"
    assert report["failed_checks"] == []
    assert report["external_blockers"] == ["production_auth_provider_activation"]


def test_auth_readiness_gate_cli_prints_machine_readable_report() -> None:
    """Operators should be able to run the auth gate before enabling billing."""
    result = subprocess.run(
        [sys.executable, "scripts/auth_readiness_gate.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["gate"] == "auth_readiness"
    assert payload["readiness_status"] == "ready"
