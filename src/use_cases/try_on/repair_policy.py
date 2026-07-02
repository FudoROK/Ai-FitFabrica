"""Backend-owned policy for Try-On repair execution."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.try_on import TryOnQualityReport


class TryOnRepairPolicyDecision(BaseModel):
    """Decision describing whether a local repair pass is allowed."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    rejection_reasons: list[str] = Field(default_factory=list)


class TryOnRepairPolicy:
    """Allow only narrow local repairs recommended by quality verification."""

    def __init__(self, *, minimum_repair_confidence: float = 0.4) -> None:
        """Store the configured minimum confidence for repair attempts."""

        if not 0.0 <= minimum_repair_confidence <= 1.0:
            raise ValueError("minimum_repair_confidence must be between 0 and 1")
        self._minimum_repair_confidence = minimum_repair_confidence

    def evaluate(self, report: TryOnQualityReport) -> TryOnRepairPolicyDecision:
        """Return whether the quality report is safe for local repair."""

        reasons: list[str] = []
        if report.verdict != "repair_recommended":
            reasons.append("repair_not_recommended")
        if not report.checks:
            reasons.append("repair_targets_missing")
        if any(check.status == "failed" for check in report.checks):
            reasons.append("failed_quality_checks_not_repairable")
        if not any(check.status == "warning" for check in report.checks):
            reasons.append("repair_targets_missing")
        if report.confidence < self._minimum_repair_confidence:
            reasons.append("repair_confidence_too_low")
        return TryOnRepairPolicyDecision(allowed=not reasons, rejection_reasons=reasons)
