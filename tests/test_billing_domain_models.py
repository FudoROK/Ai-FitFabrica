from __future__ import annotations

from src.domain.billing import BillingOwnerType, CreditAccount, LedgerEvent, WorkflowChargeRequest


def test_credit_account_keeps_available_and_reserved_balances() -> None:
    account = CreditAccount(
        owner_id="user-1",
        owner_type=BillingOwnerType.PERSON,
        available_credits=120,
        reserved_credits=15,
    )

    assert account.available_credits == 120
    assert account.reserved_credits == 15


def test_workflow_charge_request_tracks_policy_and_reference() -> None:
    charge = WorkflowChargeRequest(
        owner_id="user-1",
        owner_type=BillingOwnerType.PERSON,
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="generation_pass",
        requested_credits=12,
    )

    assert charge.workflow_reference == "job-1"
    assert charge.workflow_type == "try_on"


def test_ledger_event_exposes_balance_after_event() -> None:
    event = LedgerEvent(
        event_id="evt-1",
        owner_id="user-1",
        owner_type=BillingOwnerType.PERSON,
        event_type="charge",
        credits_delta=-12,
        balance_after_event=108,
        workflow_type="try_on",
        workflow_reference="job-1",
    )

    assert event.balance_after_event == 108
