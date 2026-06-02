"""Backend-owned billing orchestration for credits and ledger operations."""

from __future__ import annotations

from src.domain.billing import (
    BillingEventType,
    BillingOwnerType,
    CreditAccount,
    LedgerAppendRequest,
    LedgerEvent,
)
from src.use_cases.billing.policy import BillingPolicyResolver
from src.use_cases.billing.ports import BillingRepository


class BillingService:
    """Coordinate workflow charging, refunds, and ledger balance reads."""

    def __init__(
        self,
        *,
        repository: BillingRepository,
        policy_resolver: BillingPolicyResolver,
    ) -> None:
        """Store the repository and reusable pricing-policy resolver."""
        self._repository = repository
        self._policy_resolver = policy_resolver

    async def charge_workflow(
        self,
        *,
        owner_id: str,
        owner_type: BillingOwnerType,
        workflow_type: str,
        workflow_reference: str,
        stage_name: str,
        failure_owner: str | None = None,
        recovery_kind: str | None = None,
    ) -> LedgerEvent:
        """Append one durable workflow charge event using backend policy rules."""
        policy = self._policy_resolver.resolve_charge_policy(
            workflow_type=workflow_type,
            stage_name=stage_name,
            failure_owner=failure_owner,
            recovery_kind=recovery_kind,
        )
        await self._repository.ensure_account(owner_id=owner_id, owner_type=owner_type.value)
        return await self._repository.append_ledger_event(
            LedgerAppendRequest(
                owner_id=owner_id,
                owner_type=owner_type,
                event_type=BillingEventType.CHARGE,
                credits_delta=-policy.credits_to_charge,
                workflow_type=workflow_type,
                workflow_reference=workflow_reference,
                stage_name=stage_name,
                charge_policy=policy.charge_policy,
                idempotency_key=":".join(
                    [
                        owner_type.value,
                        owner_id,
                        workflow_type,
                        workflow_reference,
                        stage_name,
                        policy.charge_policy.value,
                    ]
                ),
            )
        )

    async def refund_workflow(
        self,
        *,
        owner_id: str,
        owner_type: BillingOwnerType,
        workflow_type: str,
        workflow_reference: str,
        credits_to_refund: int,
        reason: str,
    ) -> LedgerEvent:
        """Append one durable positive refund event for a workflow reference."""
        await self._repository.ensure_account(owner_id=owner_id, owner_type=owner_type.value)
        return await self._repository.append_ledger_event(
            LedgerAppendRequest(
                owner_id=owner_id,
                owner_type=owner_type,
                event_type=BillingEventType.REFUND,
                credits_delta=credits_to_refund,
                workflow_type=workflow_type,
                workflow_reference=workflow_reference,
                stage_name=reason,
                idempotency_key=":".join(
                    [owner_type.value, owner_id, workflow_type, workflow_reference, "refund", reason]
                ),
            )
        )

    async def adjust_balance(
        self,
        *,
        owner_id: str,
        owner_type: BillingOwnerType,
        credits_delta: int,
        reason: str,
    ) -> LedgerEvent:
        """Append one manual durable balance adjustment."""
        await self._repository.ensure_account(owner_id=owner_id, owner_type=owner_type.value)
        return await self._repository.append_ledger_event(
            LedgerAppendRequest(
                owner_id=owner_id,
                owner_type=owner_type,
                event_type=BillingEventType.ADJUSTMENT,
                credits_delta=credits_delta,
                stage_name=reason,
                idempotency_key=":".join([owner_type.value, owner_id, "adjustment", reason, str(credits_delta)]),
            )
        )

    async def get_account_balance(
        self,
        *,
        owner_id: str,
        owner_type: BillingOwnerType,
    ) -> CreditAccount:
        """Return the durable balance for the requested owner."""
        return await self._repository.get_balance(owner_id=owner_id, owner_type=owner_type.value)

    async def list_ledger_events(
        self,
        *,
        owner_id: str,
        owner_type: BillingOwnerType,
        limit: int = 50,
    ) -> list[LedgerEvent]:
        """Return recent durable ledger history for the requested owner."""
        return await self._repository.list_ledger_events(
            owner_id=owner_id,
            owner_type=owner_type.value,
            limit=limit,
        )
