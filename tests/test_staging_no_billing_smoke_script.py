"""Tests for the staging no-billing smoke script."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts import staging_no_billing_smoke as smoke


def test_staging_no_billing_smoke_matrix_is_safe_by_default() -> None:
    checks = smoke._check_matrix(include_demo_request=False)
    names = [check.name for check in checks]

    assert "backend_health" in names
    assert "backend_ready" in names
    assert "auth_session" in names
    assert "auth_sign_in_fail_closed" in names
    assert "frontend_home" in names
    assert "frontend_admin_readiness" in names
    assert "frontend_b2c_for_you" in names
    assert "frontend_b2c_try_on_new" in names
    assert "frontend_b2c_similar_search" in names
    assert "frontend_b2c_outfit_builder" in names
    assert "frontend_b2b_business_catalog" in names
    assert "frontend_b2b_product_card" in names
    assert "frontend_b2b_content_package" in names
    assert "frontend_b2b_admin_business_catalog" in names
    assert "demo_request_write" not in names


def test_staging_no_billing_smoke_can_include_demo_request_write() -> None:
    checks = smoke._check_matrix(include_demo_request=True)
    names = [check.name for check in checks]

    assert "demo_request_write" in names


def test_status_code_expectation_accepts_allowed_statuses() -> None:
    response = smoke.SmokeResponse(status_code=503, body={"error": {"code": "auth_not_configured"}})

    assert smoke._status_matches(response, {503}) is True
    assert smoke._status_matches(response, {200}) is False


def test_staging_no_billing_smoke_cli_lists_checks_without_network() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/staging_no_billing_smoke.py", "--list"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["smoke"] == "staging_no_billing"
    assert any(check["name"] == "backend_ready" for check in payload["checks"])
