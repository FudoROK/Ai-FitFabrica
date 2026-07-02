from src.domain.try_on import TryOnQualityCheck, TryOnQualityReport
from src.use_cases.try_on.repair_policy import TryOnRepairPolicy


def test_repair_policy_allows_local_wear_control_warning() -> None:
    report = TryOnQualityReport(
        verdict="repair_recommended",
        confidence=0.82,
        checks=[
            TryOnQualityCheck(
                name="wear_control_match",
                status="warning",
                confidence=0.82,
                message="Untucked hem is partly hidden and can be locally corrected.",
            )
        ],
        limitations=[],
    )

    decision = TryOnRepairPolicy().evaluate(report)

    assert decision.allowed is True
    assert decision.rejection_reasons == []


def test_repair_policy_rejects_blocking_wear_control_failure() -> None:
    report = TryOnQualityReport(
        verdict="reject",
        confidence=0.91,
        checks=[
            TryOnQualityCheck(
                name="wear_control_match",
                status="failed",
                confidence=0.91,
                message="Selected tucked styling is completely contradicted and needs regeneration.",
            )
        ],
        limitations=[],
    )

    decision = TryOnRepairPolicy().evaluate(report)

    assert decision.allowed is False
    assert "repair_not_recommended" in decision.rejection_reasons
    assert "failed_quality_checks_not_repairable" in decision.rejection_reasons
