"""Tests for the billing activation readiness gate."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import billing_readiness_gate as gate


def test_billing_readiness_gate_reports_safe_pre_activation_state() -> None:
    """Billing readiness should pass before activation only when billing remains disabled and guarded."""
    report = gate.run_gate()

    assert report["gate"] == "billing_readiness"
    assert report["readiness_status"] == "ready"
    assert report["failed_checks"] == []
    assert report["external_blockers"] == ["billing_core_activation", "payment_provider_activation"]


def test_billing_readiness_gate_cli_prints_machine_readable_report() -> None:
    """Operators should be able to run the billing gate before enabling billing."""
    result = subprocess.run(
        [sys.executable, "scripts/billing_readiness_gate.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["gate"] == "billing_readiness"
    assert payload["readiness_status"] == "ready"
