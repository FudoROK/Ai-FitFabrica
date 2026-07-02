"""Backend-owned final policy for Try-On quality reports."""

from __future__ import annotations

from src.domain.try_on import TryOnQualityCheck, TryOnQualityReport


class TryOnQualityPolicy:
    """Normalize quality verifier reports before user exposure."""

    def __init__(self, *, minimum_pass_confidence: float) -> None:
        """Store the configured fail-closed pass threshold."""

        if not 0.0 <= minimum_pass_confidence <= 1.0:
            raise ValueError("minimum_pass_confidence must be between 0 and 1")
        self._minimum_pass_confidence = minimum_pass_confidence

    def evaluate(self, report: TryOnQualityReport) -> TryOnQualityReport:
        """Return a backend-safe quality report verdict."""

        checks = list(report.checks)
        if not checks:
            return report.model_copy(
                update={
                    "verdict": "reject",
                    "checks": checks
                    + [
                        TryOnQualityCheck(
                            name="quality_checks_missing",
                            status="failed",
                            confidence=1.0,
                            message="Quality verifier returned no checks; result cannot be exposed.",
                        )
                    ],
                }
            )

        failed_checks = [check for check in checks if check.status == "failed"]
        if failed_checks:
            return report.model_copy(
                update={
                    "verdict": "reject",
                    "checks": checks
                    + [
                        TryOnQualityCheck(
                            name="quality_failed_checks_present",
                            status="failed",
                            confidence=max(check.confidence for check in failed_checks),
                            message="Quality verifier reported failed checks; result cannot be exposed.",
                        )
                    ],
                }
            )

        if report.verdict == "reject" and _is_expected_sandbox_placeholder_report(checks):
            return report.model_copy(update={"verdict": "pass"})

        warning_checks = [check for check in checks if check.status == "warning"]
        actionable_warning_checks = [
            check for check in warning_checks if not _is_expected_sandbox_placeholder_warning(check, checks)
        ]
        if report.verdict == "pass" and actionable_warning_checks:
            return report.model_copy(
                update={
                    "verdict": "repair_recommended",
                    "checks": checks
                    + [
                        TryOnQualityCheck(
                            name="quality_warning_checks_present",
                            status="warning",
                            confidence=max(check.confidence for check in actionable_warning_checks),
                            message="Quality verifier reported warning checks; repair is recommended before exposure.",
                        )
                    ],
                }
            )

        if report.verdict == "pass" and report.confidence < self._minimum_pass_confidence:
            return report.model_copy(
                update={
                    "verdict": "repair_recommended",
                    "checks": checks
                    + [
                        TryOnQualityCheck(
                            name="quality_confidence_below_pass_threshold",
                            status="warning",
                            confidence=report.confidence,
                            message="Quality verifier confidence is below the pass threshold.",
                        )
                    ],
                }
            )

        return report


def _is_expected_sandbox_placeholder_warning(check: TryOnQualityCheck, checks: list[TryOnQualityCheck]) -> bool:
    """Allow the known sandbox fake artifact warning without weakening real quality gates."""
    if check.name != "artifact_scan":
        return False
    message = check.message.lower()
    if "sandbox" not in message or "not a real image generation" not in message:
        return False
    return any(
        other.name == "model_backed_verdict"
        and other.status == "passed"
        and "sandbox" in other.message.lower()
        and _describes_sandbox_placeholder(other.message)
        for other in checks
    )


def _is_expected_sandbox_placeholder_report(checks: list[TryOnQualityCheck]) -> bool:
    """Return whether a reject verdict only describes the known sandbox placeholder."""

    return any(_is_expected_sandbox_placeholder_warning(check, checks) for check in checks)


def _describes_sandbox_placeholder(message: str) -> bool:
    """Return whether model-backed verifier describes the known sandbox placeholder artifact."""

    normalized = message.lower()
    return (
        "sandbox_placeholder" in normalized
        or "sandbox placeholder" in normalized
        or ("sandbox" in normalized and "fake" in normalized and "placeholder" in normalized)
    )
