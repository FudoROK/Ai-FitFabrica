"""Ports for backend-owned billing and credits orchestration."""

from __future__ import annotations

from typing import Protocol

from src.domain.billing import CreditAccount, LedgerAppendRequest, LedgerEvent


class BillingRepository(Protocol):
    """Persistence contract for credit balances and ledger events."""

    async def ensure_account(
        self,
        *,
        owner_id: str,
        owner_type: str,
        initial_credits: int = 0,
    ) -> CreditAccount:
        """Return or create the durable credit account for the requested owner."""

    async def append_ledger_event(self, request: LedgerAppendRequest) -> LedgerEvent:
        """Persist one idempotent credit ledger event and update the balance."""

    async def get_balance(self, *, owner_id: str, owner_type: str) -> CreditAccount:
        """Return the durable balance for the requested owner."""

    async def list_ledger_events(
        self,
        *,
        owner_id: str,
        owner_type: str,
        limit: int = 50,
    ) -> list[LedgerEvent]:
        """Return recent durable ledger events for the requested owner."""
