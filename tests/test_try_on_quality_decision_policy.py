from __future__ import annotations

from src.domain.try_on import TryOnQualityCheck, TryOnQualityReport
from src.use_cases.try_on.quality_decision_policy import TryOnQualityDecisionPolicy


def _report(*, verdict: str, checks: list[TryOnQualityCheck], confidence: float = 0.9) -> TryOnQualityReport:
    return TryOnQualityReport.model_validate(
        {
            "verdict": verdict,
            "confidence": confidence,
            "checks": checks,
            "limitations": [],
        }
    )


def test_quality_decision_policy_allows_safe_local_repair() -> None:
    report = _report(
        verdict="repair_recommended",
        checks=[
            TryOnQualityCheck(
                name="minor_background_artifact",
                status="warning",
                confidence=0.72,
                message="Small local background artifact near the edge.",
            )
        ],
    )

    decision = TryOnQualityDecisionPolicy().evaluate(report)

    assert decision.action == "repair"
    assert decision.reasons == ["quality_verifier_recommended_local_repair"]


def test_quality_decision_policy_routes_malformed_hands_to_retry_not_repair() -> None:
    report = _report(
        verdict="reject",
        checks=[
            TryOnQualityCheck(
                name="visual_defect_hands",
                status="failed",
                confidence=1.0,
                message="Left hand has severe anatomical distortions and malformed fingers.",
            )
        ],
    )

    decision = TryOnQualityDecisionPolicy().evaluate(report)

    assert decision.action == "retry_recommended"
    assert "blocking_generation_artifact" in decision.reasons
    assert "hands" in decision.retry_categories


def test_quality_decision_policy_rejects_identity_change_without_local_repair() -> None:
    report = _report(
        verdict="reject",
        checks=[
            TryOnQualityCheck(
                name="face_preservation",
                status="failed",
                confidence=0.95,
                message="Face identity changed compared with the source image.",
            )
        ],
    )

    decision = TryOnQualityDecisionPolicy().evaluate(report)

    assert decision.action == "reject"
    assert "identity_or_core_subject_changed" in decision.reasons

