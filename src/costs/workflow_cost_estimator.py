"""Workflow-level cost estimator for agent and generation calls."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, ConfigDict, Field


class CostedAgentInvocation(BaseModel):
    """One costed agent or generation call used by workflow summaries."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    image_input_count: int = Field(default=0, ge=0)
    image_output_count: int = Field(default=0, ge=0)
    generation_output_count: int = Field(default=0, ge=0)
    attempt_number: int = Field(default=1, ge=1)
    retry_reason: str | None = None
    repair_reason: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    validation_status: str | None = None
    estimated_provider_cost_usd: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    estimated_internal_cost_usd: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    usage_source: str = "estimated"


class WorkflowCostSummary(BaseModel):
    """Aggregated cost, revenue, and margin summary for one workflow job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: str = Field(min_length=1)
    status: str = Field(min_length=1)
    total_agent_calls: int = Field(ge=0)
    total_generation_calls: int = Field(ge=0)
    total_retry_count: int = Field(ge=0)
    total_repair_count: int = Field(ge=0)
    direct_provider_cost_usd: Decimal
    retry_cost_usd: Decimal
    repair_cost_usd: Decimal
    storage_estimated_cost_usd: Decimal
    total_internal_cost_usd: Decimal
    free_failed_job_cost_total_usd: Decimal
    credits_charged: int = Field(ge=0)
    revenue_estimated_usd: Decimal
    gross_margin_usd: Decimal
    gross_margin_percent: Decimal


class WorkflowCostEstimator:
    """Calculate reproducible workflow cost summaries from safe metadata."""

    def __init__(
        self,
        *,
        credit_value_kzt: Decimal = Decimal("50"),
        usd_to_kzt: Decimal = Decimal("500"),
        storage_estimated_cost_usd: Decimal = Decimal("0"),
    ) -> None:
        """Store currency assumptions used for reports."""

        self._credit_value_kzt = credit_value_kzt
        self._usd_to_kzt = usd_to_kzt
        self._storage_estimated_cost_usd = storage_estimated_cost_usd

    def actual_after_run(
        self,
        *,
        job_id: str,
        workflow_type: str,
        status: str,
        agent_invocations: list[CostedAgentInvocation],
        credits_charged: int,
    ) -> WorkflowCostSummary:
        """Return actual cost summary after a workflow completed or failed."""

        return self._summary(
            job_id=job_id,
            workflow_type=workflow_type,
            status=status,
            agent_invocations=agent_invocations,
            credits_charged=credits_charged,
            free_failed_job=False,
        )

    def estimate_before_run(
        self,
        *,
        job_id: str,
        workflow_type: str,
        planned_invocations: list[CostedAgentInvocation],
        planned_credits: int,
    ) -> WorkflowCostSummary:
        """Return a pre-run estimate using planned steps."""

        return self._summary(
            job_id=job_id,
            workflow_type=workflow_type,
            status="estimated",
            agent_invocations=planned_invocations,
            credits_charged=planned_credits,
            free_failed_job=False,
        )

    def failed_job_cost(
        self,
        *,
        job_id: str,
        workflow_type: str,
        failure_stage: str,
        agent_invocations: list[CostedAgentInvocation],
    ) -> WorkflowCostSummary:
        """Return failed workflow cost summary with zero user charge."""

        return self._summary(
            job_id=job_id,
            workflow_type=workflow_type,
            status="failed",
            agent_invocations=agent_invocations,
            credits_charged=0,
            free_failed_job=True,
        )

    def successful_job_cost(
        self,
        *,
        job_id: str,
        workflow_type: str,
        agent_invocations: list[CostedAgentInvocation],
        credits_charged: int,
    ) -> WorkflowCostSummary:
        """Return successful workflow cost summary."""

        return self.actual_after_run(
            job_id=job_id,
            workflow_type=workflow_type,
            status="completed",
            agent_invocations=agent_invocations,
            credits_charged=credits_charged,
        )

    def repair_cost(self, agent_invocations: list[CostedAgentInvocation]) -> Decimal:
        """Return internal repair cost from invocations with repair reason."""

        return _money(sum((item.estimated_internal_cost_usd for item in agent_invocations if item.repair_reason), Decimal("0")))

    def retry_cost(self, agent_invocations: list[CostedAgentInvocation]) -> Decimal:
        """Return internal retry cost from invocations with retry reason."""

        return _money(sum((item.estimated_internal_cost_usd for item in agent_invocations if item.retry_reason), Decimal("0")))

    def _summary(
        self,
        *,
        job_id: str,
        workflow_type: str,
        status: str,
        agent_invocations: list[CostedAgentInvocation],
        credits_charged: int,
        free_failed_job: bool,
    ) -> WorkflowCostSummary:
        provider_cost = _money(sum((item.estimated_provider_cost_usd for item in agent_invocations), Decimal("0")))
        retry_cost = self.retry_cost(agent_invocations)
        repair_cost = self.repair_cost(agent_invocations)
        internal_cost = _money(
            sum((item.estimated_internal_cost_usd for item in agent_invocations), Decimal("0"))
            + self._storage_estimated_cost_usd
        )
        revenue = self._revenue_usd(credits_charged)
        margin = _money(revenue - internal_cost)
        return WorkflowCostSummary(
            job_id=job_id,
            workflow_type=workflow_type,
            status=status,
            total_agent_calls=len(agent_invocations),
            total_generation_calls=sum(1 for item in agent_invocations if item.generation_output_count > 0),
            total_retry_count=sum(1 for item in agent_invocations if item.retry_reason),
            total_repair_count=sum(1 for item in agent_invocations if item.repair_reason),
            direct_provider_cost_usd=provider_cost,
            retry_cost_usd=retry_cost,
            repair_cost_usd=repair_cost,
            storage_estimated_cost_usd=_money(self._storage_estimated_cost_usd),
            total_internal_cost_usd=internal_cost,
            free_failed_job_cost_total_usd=internal_cost if free_failed_job else Decimal("0.000000"),
            credits_charged=credits_charged,
            revenue_estimated_usd=revenue,
            gross_margin_usd=margin,
            gross_margin_percent=self._margin_percent(revenue=revenue, margin=margin),
        )

    def _revenue_usd(self, credits_charged: int) -> Decimal:
        kzt = Decimal(credits_charged) * self._credit_value_kzt
        return _money(kzt / self._usd_to_kzt)

    @staticmethod
    def _margin_percent(*, revenue: Decimal, margin: Decimal) -> Decimal:
        if revenue <= 0:
            return Decimal("0.00")
        return (margin / revenue * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _money(value: Decimal) -> Decimal:
    """Normalize USD amounts to six decimals."""

    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
