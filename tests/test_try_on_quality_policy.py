from __future__ import annotations

import pytest

from src.domain.try_on import TryOnQualityCheck, TryOnQualityReport
from src.use_cases.try_on.quality_policy import TryOnQualityPolicy


def _report(**overrides: object) -> TryOnQualityReport:
    payload: dict[str, object] = {
        "verdict": "pass",
        "confidence": 0.86,
        "checks": [
            TryOnQualityCheck(
                name="generated_artifact_reference",
                status="passed",
                confidence=0.9,
                message="Generated artifact reference exists.",
            ),
            TryOnQualityCheck(
                name="generated_artifact_non_empty",
                status="passed",
                confidence=0.88,
                message="Generated artifact bytes loaded.",
            ),
        ],
        "limitations": [],
    }
    payload.update(overrides)
    return TryOnQualityReport.model_validate(payload)


def test_quality_policy_allows_high_confidence_pass() -> None:
    report = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(_report())

    assert report.verdict == "pass"


def test_quality_policy_allows_expected_sandbox_placeholder_warning() -> None:
    report = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(
        _report(
            checks=[
                TryOnQualityCheck(
                    name="face_preservation",
                    status="passed",
                    confidence=0.92,
                    message="Sandbox verifier confirms the face-preservation check shape.",
                ),
                TryOnQualityCheck(
                    name="artifact_scan",
                    status="warning",
                    confidence=0.74,
                    message="Sandbox output is deterministic and not a real image generation.",
                ),
                TryOnQualityCheck(
                    name="model_backed_verdict",
                    status="passed",
                    confidence=0.91,
                    message="The try-on generation is a sandbox fake with sandbox_placeholder result image kind.",
                ),
            ]
        )
    )

    assert report.verdict == "pass"
    assert not any(check.name == "quality_warning_checks_present" for check in report.checks)


def test_quality_policy_allows_expected_sandbox_placeholder_warning_with_human_wording() -> None:
    report = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(
        _report(
            checks=[
                TryOnQualityCheck(
                    name="artifact_scan",
                    status="warning",
                    confidence=0.74,
                    message="Sandbox output is deterministic and not a real image generation.",
                ),
                TryOnQualityCheck(
                    name="model_backed_verdict",
                    status="passed",
                    confidence=0.91,
                    message="This is a sandbox placeholder generation. All sandbox-specific checks have passed.",
                ),
            ]
        )
    )

    assert report.verdict == "pass"
    assert not any(check.name == "quality_warning_checks_present" for check in report.checks)


def test_quality_policy_allows_expected_sandbox_fake_placeholder_warning_from_staging() -> None:
    report = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(
        _report(
            confidence=1.0,
            checks=[
                TryOnQualityCheck(
                    name="artifact_scan",
                    status="warning",
                    confidence=0.74,
                    message="Sandbox output is deterministic and not a real image generation.",
                ),
                TryOnQualityCheck(
                    name="model_backed_verdict",
                    status="passed",
                    confidence=1.0,
                    message=(
                        "The generation is a sandbox fake and a placeholder, not a real try-on image. "
                        "It should be rejected as it does not evaluate uploaded pixels."
                    ),
                ),
            ],
        )
    )

    assert report.verdict == "pass"
    assert not any(check.name == "quality_warning_checks_present" for check in report.checks)


def test_quality_policy_normalizes_expected_sandbox_placeholder_reject_from_staging() -> None:
    report = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(
        _report(
            verdict="reject",
            confidence=1.0,
            checks=[
                TryOnQualityCheck(
                    name="face_preservation",
                    status="passed",
                    confidence=0.92,
                    message="Sandbox verifier confirms the face-preservation check shape.",
                ),
                TryOnQualityCheck(
                    name="garment_similarity",
                    status="passed",
                    confidence=0.9,
                    message="Sandbox verifier confirms garment-similarity reporting shape.",
                ),
                TryOnQualityCheck(
                    name="artifact_scan",
                    status="warning",
                    confidence=0.74,
                    message="Sandbox output is deterministic and not a real image generation.",
                ),
                TryOnQualityCheck(
                    name="model_backed_verdict",
                    status="passed",
                    confidence=1.0,
                    message=(
                        "The generation is a sandbox fake and a placeholder, not a real try-on image. "
                        "It should be rejected as it does not evaluate uploaded pixels."
                    ),
                ),
            ],
        )
    )

    assert report.verdict == "pass"
    assert not any(check.name == "quality_warning_checks_present" for check in report.checks)


@pytest.mark.parametrize(
    ("report", "expected_verdict", "expected_check"),
    [
        (
            _report(confidence=0.4),
            "repair_recommended",
            "quality_confidence_below_pass_threshold",
        ),
        (
            _report(checks=[]),
            "reject",
            "quality_checks_missing",
        ),
        (
            _report(
                checks=[
                    TryOnQualityCheck(
                        name="face_preservation",
                        status="failed",
                        confidence=0.91,
                        message="Face changed.",
                    )
                ]
            ),
            "reject",
            "quality_failed_checks_present",
        ),
        (
            _report(
                checks=[
                    TryOnQualityCheck(
                        name="generated_artifact_size_sanity",
                        status="warning",
                        confidence=0.58,
                        message="Generated artifact is tiny.",
                    )
                ]
            ),
            "repair_recommended",
            "quality_warning_checks_present",
        ),
    ],
)
def test_quality_policy_overrides_unsafe_pass(report: TryOnQualityReport, expected_verdict: str, expected_check: str) -> None:
    evaluated = TryOnQualityPolicy(minimum_pass_confidence=0.8).evaluate(report)

    assert evaluated.verdict == expected_verdict
    assert any(check.name == expected_check for check in evaluated.checks)
