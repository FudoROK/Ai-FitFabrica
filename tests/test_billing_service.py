from __future__ import annotations

import pytest

from src.adapters.billing.in_memory_repository import InMemoryBillingRepository
from src.domain.billing import BillingOwnerType
from src.use_cases.billing.policy import BillingPolicyResolver
from src.use_cases.billing.service import BillingService


@pytest.mark.asyncio
async def test_billing_service_charges_standard_workflow_cost() -> None:
    repository = InMemoryBillingRepository()
    await repository.ensure_account(owner_id="user-1", owner_type="person", initial_credits=100)
    service = BillingService(
        repository=repository,
        policy_resolver=BillingPolicyResolver(workflow_base_costs={"try_on": 12}),
    )

    event = await service.charge_workflow(
        owner_id="user-1",
        owner_type=BillingOwnerType.PERSON,
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="completed",
    )

    assert event.credits_delta == -12
    assert event.balance_after_event == 88


@pytest.mark.asyncio
async def test_billing_service_returns_zero_charge_for_free_retry() -> None:
    repository = InMemoryBillingRepository()
    await repository.ensure_account(owner_id="user-1", owner_type="person", initial_credits=100)
    service = BillingService(
        repository=repository,
        policy_resolver=BillingPolicyResolver(workflow_base_costs={"try_on": 12}),
    )

    event = await service.charge_workflow(
        owner_id="user-1",
        owner_type=BillingOwnerType.PERSON,
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="retry_after_system_failure",
        failure_owner="system",
        recovery_kind="retry",
    )

    assert event.credits_delta == 0
    assert event.balance_after_event == 100
