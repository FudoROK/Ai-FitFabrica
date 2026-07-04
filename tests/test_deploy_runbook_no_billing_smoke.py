"""Guardrails for no-billing staging smoke coverage in deploy docs."""

from pathlib import Path


def test_deploy_runbook_mentions_no_billing_gates() -> None:
    source = Path("docs/runbooks/deploy_backend_and_frontend_ru.md").read_text(encoding="utf-8")

    assert "scripts/no_billing_acceptance_gate.py" in source
    assert "scripts/staging_no_billing_smoke.py" in source
    assert "--status-token" in source
    assert "--include-demo-request" in source
