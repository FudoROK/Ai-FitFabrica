"""Workflow service for backend-owned pricing recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.billing import BillingOwnerType, LedgerEvent
from src.domain.pricing import PricingJobRecord, PricingRecommendationRecord, PricingRequest
from src.use_cases.pricing.query_preparation import build_pricing_brief
from src.use_cases.pricing.ranking import recommend_price


@dataclass(frozen=True)
class PricingWorkflowResult:
    """Structured workflow result returned by the pricing service."""

    job: PricingJobRecord
    recommendation: PricingRecommendationRecord
    ledger_event: LedgerEvent | None = None


class PricingWorkflowService:
    """Orchestrate market evidence lookup, recommendation, and workflow storage for pricing jobs."""

    def __init__(
        self,
        *,
        repository,
        comparison_source,
        clock,
        billing_service=None,
        billing_owner_id: str = "public-business",
        billing_owner_type: BillingOwnerType = BillingOwnerType.BUSINESS,
    ) -> None:
        """Store explicit dependencies for pricing orchestration."""
        self._repository = repository
        self._comparison_source = comparison_source
        self._clock = clock
        self._billing_service = billing_service
        self._billing_owner_id = billing_owner_id
        self._billing_owner_type = billing_owner_type

    async def create_pricing_recommendation(self, *, request: PricingRequest) -> PricingWorkflowResult:
        """Build one pricing recommendation from comparable market evidence and persist it."""
        job = await self.create_pricing_job(request=request)
        return await self.execute_pricing_job(job_id=job.job_id, job=job)

    async def create_pricing_job(self, *, request: PricingRequest) -> PricingJobRecord:
        """Create one accepted pricing job without running recommendation logic."""
        return await self._repository.create_job(request=request, now=self._clock())

    async def execute_pricing_job(
        self,
        *,
        job_id: str,
        job: PricingJobRecord | None = None,
    ) -> PricingWorkflowResult:
        """Execute recommendation generation for an existing accepted pricing job."""
        job = job or await self._repository.get_job(job_id)
        if job is None:
            raise LookupError(f"Unknown pricing job: {job_id}")
        request = PricingRequest(
            product_id=job.product_id,
            target_currency=job.target_currency,
            desired_margin_percent=job.desired_margin_percent,
        )
        brief = build_pricing_brief(request)
        comparables = await self._comparison_source.list_comparables(brief)
        recommendation = recommend_price(
            comparables=[item.price_amount for item in comparables],
            desired_margin_percent=brief.desired_margin_percent,
            currency=brief.target_currency,
        )
        saved = await self._repository.save_recommendation(
            job_id=job.job_id,
            recommendation=recommendation,
            now=self._clock(),
        )
        completed = await self._repository.mark_completed(job.job_id, now=self._clock())
        ledger_event = await self._charge_completed_job(job_id=job.job_id)
        return PricingWorkflowResult(job=completed, recommendation=saved, ledger_event=ledger_event)

    async def get_job(self, job_id: str) -> PricingJobRecord | None:
        """Return the persisted pricing job for the requested identifier."""
        return await self._repository.get_job(job_id)

    async def get_result(self, job_id: str) -> PricingRecommendationRecord | None:
        """Return the latest persisted pricing recommendation for the requested job identifier."""
        return await self._repository.get_latest_recommendation(job_id)

    async def _charge_completed_job(self, *, job_id: str) -> LedgerEvent | None:
        """Charge the completed pricing workflow through the billing core when configured."""
        if self._billing_service is None:
            return None
        return await self._billing_service.charge_workflow(
            owner_id=self._billing_owner_id,
            owner_type=self._billing_owner_type,
            workflow_type="pricing",
            workflow_reference=job_id,
            stage_name="completed",
        )
