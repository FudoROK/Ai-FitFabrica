from __future__ import annotations

import pytest

from src.domain.try_on import TryOnQualityCheck, TryOnQualityReport
from src.use_cases.try_on.repair_policy import TryOnRepairPolicy


def _report(**overrides: object) -> TryOnQualityReport:
    payload: dict[str, object] = {
        "verdict": "repair_recommended",
        "confidence": 0.61,
        "checks": [
            TryOnQualityCheck(
                name="generated_artifact_size_sanity",
                status="warning",
                confidence=0.58,
                message="Generated artifact is very small.",
            )
        ],
        "limitations": ["A local backend repair pass is recommended."],
    }
    payload.update(overrides)
    return TryOnQualityReport.model_validate(payload)


def test_repair_policy_allows_local_warning_repair() -> None:
    decision = TryOnRepairPolicy().evaluate(_report())

    assert decision.allowed is True
    assert decision.rejection_reasons == []


@pytest.mark.parametrize(
    ("report", "reason"),
    [
        (_report(verdict="pass"), "repair_not_recommended"),
        (
            _report(
                checks=[
                    TryOnQualityCheck(
                        name="face_preservation",
                        status="failed",
                        confidence=0.9,
                        message="Face changed.",
                    )
                ]
            ),
            "failed_quality_checks_not_repairable",
        ),
        (_report(checks=[]), "repair_targets_missing"),
        (_report(confidence=0.2), "repair_confidence_too_low"),
    ],
)
def test_repair_policy_blocks_unsafe_repair(report: TryOnQualityReport, reason: str) -> None:
    decision = TryOnRepairPolicy().evaluate(report)

    assert decision.allowed is False
    assert reason in decision.rejection_reasons
