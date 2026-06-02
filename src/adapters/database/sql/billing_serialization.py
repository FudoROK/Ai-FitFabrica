"""Serialization helpers for billing SQL rows and domain models."""

from __future__ import annotations

from src.domain.billing import (
    BillingChargePolicy,
    BillingEventType,
    BillingOwnerType,
    CreditAccount,
    LedgerEvent,
)

from .billing_models import CreditAccountRow, CreditLedgerEventRow


def account_from_row(row: CreditAccountRow) -> CreditAccount:
    """Convert one durable credit-account row into the domain model."""
    return CreditAccount(
        owner_id=row.owner_id,
        owner_type=BillingOwnerType(row.owner_type),
        available_credits=row.available_credits,
        reserved_credits=row.reserved_credits,
    )


def ledger_event_from_row(row: CreditLedgerEventRow, *, owner_id: str, owner_type: str) -> LedgerEvent:
    """Convert one durable credit-ledger row into the domain model."""
    return LedgerEvent(
        event_id=row.event_id,
        owner_id=owner_id,
        owner_type=BillingOwnerType(owner_type),
        event_type=BillingEventType(row.event_type),
        credits_delta=row.credits_delta,
        balance_after_event=row.balance_after_event,
        workflow_type=row.workflow_type,
        workflow_reference=row.workflow_reference,
        stage_name=row.stage_name,
        charge_policy=BillingChargePolicy(row.charge_policy) if row.charge_policy else None,
        created_at=row.created_at,
    )
