from __future__ import annotations

from decimal import Decimal

from src.costs.workflow_cost_estimator import CostedAgentInvocation, WorkflowCostEstimator


def test_workflow_cost_estimator_summarizes_successful_job_margin() -> None:
    estimator = WorkflowCostEstimator(credit_value_kzt=Decimal("50"), usd_to_kzt=Decimal("500"))

    summary = estimator.actual_after_run(
        job_id="try_on_1",
        workflow_type="try_on",
        status="completed",
        agent_invocations=[
            CostedAgentInvocation(
                agent_name="human_identity_agent",
                provider="gemini",
                model="gemini-2.5-flash",
                input_tokens=10_000,
                output_tokens=1_000,
                estimated_provider_cost_usd=Decimal("0.0055"),
                estimated_internal_cost_usd=Decimal("0.0066"),
            ),
            CostedAgentInvocation(
                agent_name="try_on_generation",
                provider="google_vertex",
                model="virtual-try-on-estimate",
                generation_output_count=1,
                estimated_provider_cost_usd=Decimal("0.0400"),
                estimated_internal_cost_usd=Decimal("0.0480"),
            ),
        ],
        credits_charged=12,
    )

    assert summary.total_agent_calls == 2
    assert summary.total_generation_calls == 1
    assert summary.direct_provider_cost_usd == Decimal("0.045500")
    assert summary.total_internal_cost_usd == Decimal("0.054600")
    assert summary.credits_charged == 12
    assert summary.revenue_estimated_usd == Decimal("1.200000")
    assert summary.gross_margin_usd == Decimal("1.145400")
    assert summary.gross_margin_percent == Decimal("95.45")


def test_workflow_cost_estimator_keeps_failed_before_generation_free_to_user() -> None:
    estimator = WorkflowCostEstimator(credit_value_kzt=Decimal("50"), usd_to_kzt=Decimal("500"))

    summary = estimator.failed_job_cost(
        job_id="try_on_bad_input",
        workflow_type="try_on",
        failure_stage="human_identity_analysis",
        agent_invocations=[
            CostedAgentInvocation(
                agent_name="human_identity_agent",
                provider="gemini",
                model="gemini-2.5-flash",
                input_tokens=10_000,
                output_tokens=1_000,
                estimated_provider_cost_usd=Decimal("0.0055"),
                estimated_internal_cost_usd=Decimal("0.0066"),
            )
        ],
    )

    assert summary.status == "failed"
    assert summary.credits_charged == 0
    assert summary.free_failed_job_cost_total_usd == Decimal("0.006600")
    assert summary.gross_margin_usd == Decimal("-0.006600")


def test_workflow_cost_estimator_tracks_retry_and_repair_costs_separately() -> None:
    estimator = WorkflowCostEstimator(credit_value_kzt=Decimal("50"), usd_to_kzt=Decimal("500"))

    summary = estimator.actual_after_run(
        job_id="try_on_repair",
        workflow_type="try_on",
        status="completed",
        agent_invocations=[
            CostedAgentInvocation(
                agent_name="repair_agent",
                provider="gemini",
                model="gemini-2.5-flash",
                estimated_provider_cost_usd=Decimal("0.0100"),
                estimated_internal_cost_usd=Decimal("0.0120"),
                repair_reason="quality_failure",
            ),
            CostedAgentInvocation(
                agent_name="try_on_agent",
                provider="gemini",
                model="gemini-2.5-flash",
                estimated_provider_cost_usd=Decimal("0.0200"),
                estimated_internal_cost_usd=Decimal("0.0240"),
                retry_reason="provider_error",
            ),
        ],
        credits_charged=12,
    )

    assert summary.total_retry_count == 1
    assert summary.total_repair_count == 1
    assert summary.retry_cost_usd == Decimal("0.024000")
    assert summary.repair_cost_usd == Decimal("0.012000")
