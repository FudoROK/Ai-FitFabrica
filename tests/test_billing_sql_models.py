from __future__ import annotations

from src.adapters.database.sql.billing_models import (
    CreditAccountRow,
    CreditLedgerEventRow,
    WorkflowPricingRuleRow,
)


def test_billing_sql_models_define_account_ledger_and_policy_tables() -> None:
    assert CreditAccountRow.__tablename__ == "credit_accounts"
    assert CreditLedgerEventRow.__tablename__ == "credit_ledger_events"
    assert WorkflowPricingRuleRow.__tablename__ == "workflow_pricing_rules"
