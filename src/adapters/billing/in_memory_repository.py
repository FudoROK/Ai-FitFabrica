"""In-memory fallback repository for backend-owned billing and credits."""

from __future__ import annotations

from src.domain.billing import (
    BillingOwnerType,
    CreditAccount,
    LedgerAppendRequest,
    LedgerEvent,
)


class InMemoryBillingRepository:
    """Store credit balances and ledger events in memory when SQL is unavailable."""

    def __init__(self) -> None:
        """Initialize durable-looking in-memory account and event stores."""
        self._accounts: dict[tuple[str, str], CreditAccount] = {}
        self._events: dict[tuple[str, str], list[LedgerEvent]] = {}
        self._idempotency_events: dict[str, LedgerEvent] = {}

    async def ensure_account(
        self,
        *,
        owner_id: str,
        owner_type: str,
        initial_credits: int = 0,
    ) -> CreditAccount:
        """Return or create an in-memory credit account for the requested owner."""
        key = (owner_type, owner_id)
        account = self._accounts.get(key)
        if account is None:
            account = CreditAccount(
                owner_id=owner_id,
                owner_type=BillingOwnerType(owner_type),
                available_credits=initial_credits,
                reserved_credits=0,
            )
            self._accounts[key] = account
        return account

    async def append_ledger_event(self, request: LedgerAppendRequest) -> LedgerEvent:
        """Append one idempotent in-memory ledger event and update the account balance."""
        existing = self._idempotency_events.get(request.idempotency_key)
        if existing is not None:
            return existing

        key = (request.owner_type.value, request.owner_id)
        account = await self.ensure_account(owner_id=request.owner_id, owner_type=request.owner_type.value)
        next_balance = account.available_credits + request.credits_delta
        if next_balance < 0:
            raise ValueError("Credit balance cannot become negative")

        event = LedgerEvent(
            event_id=f"billing_evt_{len(self._idempotency_events) + 1}",
            owner_id=request.owner_id,
            owner_type=request.owner_type,
            event_type=request.event_type,
            credits_delta=request.credits_delta,
            balance_after_event=next_balance,
            workflow_type=request.workflow_type,
            workflow_reference=request.workflow_reference,
            stage_name=request.stage_name,
            charge_policy=request.charge_policy,
            created_at=request.created_at,
        )
        self._accounts[key] = account.model_copy(update={"available_credits": next_balance})
        self._events.setdefault(key, []).append(event)
        self._idempotency_events[request.idempotency_key] = event
        return event

    async def get_balance(self, *, owner_id: str, owner_type: str) -> CreditAccount:
        """Return the current in-memory balance for the requested owner."""
        return await self.ensure_account(owner_id=owner_id, owner_type=owner_type)

    async def list_ledger_events(
        self,
        *,
        owner_id: str,
        owner_type: str,
        limit: int = 50,
    ) -> list[LedgerEvent]:
        """Return recent in-memory ledger events for the requested owner."""
        key = (owner_type, owner_id)
        return list(reversed(self._events.get(key, [])))[:limit]
