import pytest
from pydantic import ValidationError

from src.adk_agents.quality_verifier_agent.contracts import (
    QualityCategoryScore,
    QualityDefect,
    QualityVerdict,
    QualityVerifierDecisionContract,
)
from src.domain.try_on import TryOnQualityCheck, TryOnQualityReport
from src.use_cases.try_on.quality_policy import TryOnQualityPolicy


def test_quality_verifier_contract_accepts_wear_control_match_category() -> None:
    contract = QualityVerifierDecisionContract(
        verdict=QualityVerdict.REPAIR_RECOMMENDED,
        summary="Selected untucked control is partly violated.",
        confidence=0.84,
        repair_targets=["Lower shirt hem should remain visible over the waistband."],
        defects=[
            QualityDefect(
                defect_type="wear_control",
                region="waist",
                severity="minor",
                evidence="The generated shirt hem is partially tucked into the jeans.",
                repairable=True,
                confidence=0.86,
            )
        ],
        category_scores=[
            QualityCategoryScore(
                category="wear_control_match",
                score=0.62,
                evidence="Requested untucked styling is not fully preserved.",
            )
        ],
    )

    assert contract.defects[0].defect_type == "wear_control"
    assert contract.category_scores[0].category == "wear_control_match"


def test_quality_verifier_contract_rejects_pass_with_blocking_wear_control_defect() -> None:
    with pytest.raises(ValidationError, match="pass verdict cannot contain blocking defects"):
        QualityVerifierDecisionContract(
            verdict=QualityVerdict.PASS,
            summary="Looks fine.",
            confidence=0.9,
            defects=[
                QualityDefect(
                    defect_type="wear_control",
                    region="waist",
                    severity="blocking",
                    evidence="Selected tucked control is visibly ignored.",
                    repairable=False,
                    confidence=0.91,
                )
            ],
        )


def test_quality_policy_does_not_clean_pass_wear_control_warning() -> None:
    report = TryOnQualityReport(
        verdict="pass",
        confidence=0.91,
        checks=[
            TryOnQualityCheck(
                name="wear_control_match",
                status="warning",
                confidence=0.74,
                message="Requested untucked styling is partially violated.",
            )
        ],
        limitations=[],
    )

    evaluated = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(report)

    assert evaluated.verdict == "repair_recommended"
    assert evaluated.checks[-1].name == "quality_warning_checks_present"


def test_quality_policy_rejects_blocking_wear_control_failure() -> None:
    report = TryOnQualityReport(
        verdict="pass",
        confidence=0.93,
        checks=[
            TryOnQualityCheck(
                name="wear_control_match",
                status="failed",
                confidence=0.9,
                message="Requested tucked styling is visibly contradicted.",
            )
        ],
        limitations=[],
    )

    evaluated = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(report)

    assert evaluated.verdict == "reject"
    assert evaluated.checks[-1].name == "quality_failed_checks_present"
