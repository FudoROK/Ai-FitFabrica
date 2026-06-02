"""SQL-backed repositories for billing and credits persistence."""

from __future__ import annotations

from sqlalchemy import select

from src.domain.billing import BillingOwnerType, CreditAccount, LedgerAppendRequest, LedgerEvent

from .billing_models import CreditAccountRow, CreditLedgerEventRow
from .billing_serialization import account_from_row, ledger_event_from_row


class SqlBillingRepository:
    """Persist credit accounts and ledger events in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async SQL session factory."""
        self._session_factory = session_factory

    async def ensure_account(
        self,
        *,
        owner_id: str,
        owner_type: str,
        initial_credits: int = 0,
    ) -> CreditAccount:
        """Return or create the durable credit account for the requested owner."""
        async with self._session_factory() as session:
            row = (
                await session.scalars(
                    select(CreditAccountRow).where(
                        CreditAccountRow.owner_id == owner_id,
                        CreditAccountRow.owner_type == owner_type,
                    )
                )
            ).first()
            if row is None:
                row = CreditAccountRow(
                    account_id=f"{owner_type}_{owner_id}",
                    owner_id=owner_id,
                    owner_type=owner_type,
                    available_credits=initial_credits,
                    reserved_credits=0,
                )
                session.add(row)
                await session.commit()
            return account_from_row(row)

    async def append_ledger_event(self, request: LedgerAppendRequest) -> LedgerEvent:
        """Persist one idempotent durable ledger event and update the balance."""
        async with self._session_factory() as session:
            existing = (
                await session.scalars(
                    select(CreditLedgerEventRow).where(
                        CreditLedgerEventRow.idempotency_key == request.idempotency_key
                    )
                )
            ).first()
            if existing is not None:
                account = await self._get_account_row(
                    session=session,
                    owner_id=request.owner_id,
                    owner_type=request.owner_type.value,
                )
                return ledger_event_from_row(
                    existing,
                    owner_id=account.owner_id,
                    owner_type=account.owner_type,
                )

            account = await self._get_or_create_account_row(
                session=session,
                owner_id=request.owner_id,
                owner_type=request.owner_type.value,
            )
            next_balance = account.available_credits + request.credits_delta
            if next_balance < 0:
                raise ValueError("Credit balance cannot become negative")
            account.available_credits = next_balance
            row = CreditLedgerEventRow(
                event_id=f"billing_evt_{request.idempotency_key}",
                account_id=account.account_id,
                event_type=request.event_type.value,
                credits_delta=request.credits_delta,
                balance_after_event=next_balance,
                workflow_type=request.workflow_type,
                workflow_reference=request.workflow_reference,
                stage_name=request.stage_name,
                charge_policy=request.charge_policy.value if request.charge_policy else None,
                idempotency_key=request.idempotency_key,
                created_at=request.created_at,
            )
            session.add(row)
            await session.commit()
            return ledger_event_from_row(row, owner_id=account.owner_id, owner_type=account.owner_type)

    async def get_balance(self, *, owner_id: str, owner_type: str) -> CreditAccount:
        """Return the durable balance for the requested owner."""
        account = await self.ensure_account(owner_id=owner_id, owner_type=owner_type)
        return account

    async def list_ledger_events(
        self,
        *,
        owner_id: str,
        owner_type: str,
        limit: int = 50,
    ) -> list[LedgerEvent]:
        """Return recent durable ledger events for the requested owner."""
        async with self._session_factory() as session:
            account = await self._get_or_create_account_row(session=session, owner_id=owner_id, owner_type=owner_type)
            rows = list(
                (
                    await session.scalars(
                        select(CreditLedgerEventRow)
                        .where(CreditLedgerEventRow.account_id == account.account_id)
                        .order_by(CreditLedgerEventRow.created_at.desc())
                        .limit(limit)
                    )
                ).all()
            )
            return [
                ledger_event_from_row(row, owner_id=account.owner_id, owner_type=account.owner_type)
                for row in rows
            ]

    async def _get_account_row(self, *, session, owner_id: str, owner_type: str) -> CreditAccountRow:
        """Load the durable account row for the requested owner."""
        row = (
            await session.scalars(
                select(CreditAccountRow).where(
                    CreditAccountRow.owner_id == owner_id,
                    CreditAccountRow.owner_type == owner_type,
                )
            )
        ).first()
        if row is None:
            raise LookupError(f"Unknown credit account: {owner_type}:{owner_id}")
        return row

    async def _get_or_create_account_row(self, *, session, owner_id: str, owner_type: str) -> CreditAccountRow:
        """Load or create the durable account row for the requested owner."""
        row = (
            await session.scalars(
                select(CreditAccountRow).where(
                    CreditAccountRow.owner_id == owner_id,
                    CreditAccountRow.owner_type == owner_type,
                )
            )
        ).first()
        if row is None:
            row = CreditAccountRow(
                account_id=f"{owner_type}_{owner_id}",
                owner_id=owner_id,
                owner_type=owner_type,
                available_credits=0,
                reserved_credits=0,
            )
            session.add(row)
            await session.flush()
        return row
