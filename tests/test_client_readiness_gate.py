"""Tests for the B2C/B2B client readiness gate."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import client_readiness_gate as gate


def test_flow_matrix_covers_b2c_and_b2b_customer_contours() -> None:
    """The gate must cover every customer contour we plan to test before billing."""
    matrix = gate.build_flow_matrix()
    flow_ids = {flow["id"] for flow in matrix}

    assert {
        "b2c_public_entry",
        "b2c_try_on",
        "b2c_similar_search",
        "b2c_outfit_builder",
        "b2b_business_catalog",
        "b2b_product_card",
        "b2b_content_package",
        "b2b_pricing",
        "b2b_admin_review",
    }.issubset(flow_ids)


def test_local_gate_reports_ready_when_all_required_artifacts_exist() -> None:
    """Local readiness should pass when routes, APIs, tests, and runbooks are present."""
    report = gate.run_gate()

    assert report["gate"] == "client_readiness"
    assert report["readiness_status"] == "ready"
    assert report["failed_checks"] == []
    assert report["external_blockers"] == [
        "production_auth_activation",
        "billing_core_activation",
        "live_ai_provider_acceptance",
        "approved_marketplace_source_activation",
        "deployed_staging_browser_acceptance",
    ]


def test_client_readiness_cli_prints_machine_readable_report() -> None:
    """Operators should be able to run the gate from PowerShell before billing."""
    result = subprocess.run(
        [sys.executable, "scripts/client_readiness_gate.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["gate"] == "client_readiness"
    assert report["readiness_status"] == "ready"
