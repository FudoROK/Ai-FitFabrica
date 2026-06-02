from __future__ import annotations

from pathlib import Path


def test_workflow_services_do_not_construct_billing_policy_directly() -> None:
    for relative_path in [
        "src/use_cases/try_on/workflow_service.py",
        "src/use_cases/product_card/workflow_service.py",
        "src/use_cases/content_package/workflow_service.py",
        "src/use_cases/pricing/workflow_service.py",
    ]:
        text = Path(relative_path).read_text(encoding="utf-8")
        assert "BillingPolicyResolver(" not in text


def test_credit_routes_do_not_compute_balances_inline() -> None:
    text = Path("src/entrypoints/credits_routes.py").read_text(encoding="utf-8")
    assert "available_credits -" not in text
    assert "credits_delta =" not in text
