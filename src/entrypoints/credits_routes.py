"""FastAPI routes for backend-owned credit balances and ledger history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from src.domain.billing import BillingOwnerType, CreditLedgerResponse
from src.entrypoints.runtime_dependencies import billing_runtime_dependencies
from src.settings import Settings

router = APIRouter()


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


@router.get("/api/credits/{owner_type}/{owner_id}")
async def get_credit_balance(
    owner_type: BillingOwnerType,
    owner_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the backend-owned credit balance for one account owner."""
    runtime = billing_runtime_dependencies(settings)
    return await runtime.billing_service.get_account_balance(owner_id=owner_id, owner_type=owner_type)


@router.get("/api/credits/{owner_type}/{owner_id}/ledger")
async def get_credit_ledger(
    owner_type: BillingOwnerType,
    owner_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    limit: int = Query(default=50, ge=1, le=200),
) -> CreditLedgerResponse:
    """Return recent backend-owned ledger events for one account owner."""
    runtime = billing_runtime_dependencies(settings)
    events = await runtime.billing_service.list_ledger_events(
        owner_id=owner_id,
        owner_type=owner_type,
        limit=limit,
    )
    return CreditLedgerResponse(owner_id=owner_id, owner_type=owner_type, events=events)
