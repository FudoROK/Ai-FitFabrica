"""Backend-owned decision policy for Try-On quality failures."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.domain.try_on import TryOnQualityReport
from src.use_cases.try_on.repair_policy import TryOnRepairPolicy

TryOnQualityDecisionAction = Literal["pass", "repair", "retry_recommended", "reject"]

_RETRY_CHECK_TOKENS = {
    "anatomy": "anatomy",
    "body": "body",
    "finger": "hands",
    "fingers": "hands",
    "garment_similarity": "garment",
    "hand": "hands",
    "hands": "hands",
    "pose": "pose",
    "severe": "severe_artifact",
    "visual_defect_hands": "hands",
}
_REJECT_CHECK_NAMES = {
    "body_preservation",
    "face_preservation",
    "identity_preservation",
    "person_preservation",
}


class TryOnQualityDecision(BaseModel):
    """Workflow action chosen by backend after quality verification."""

    model_config = ConfigDict(extra="forbid")

    action: TryOnQualityDecisionAction
    reasons: list[str] = Field(default_factory=list)
    retry_categories: list[str] = Field(default_factory=list)


class TryOnQualityDecisionPolicy:
    """Classify a quality report into backend workflow actions."""

    def __init__(self, *, repair_policy: TryOnRepairPolicy | None = None) -> None:
        """Store explicit child policies."""

        self._repair_policy = repair_policy or TryOnRepairPolicy()

    def evaluate(self, report: TryOnQualityReport) -> TryOnQualityDecision:
        """Return the workflow decision for the verified generated result."""

        if report.verdict == "pass":
            return TryOnQualityDecision(action="pass")
        if report.verdict == "repair_recommended":
            repair_decision = self._repair_policy.evaluate(report)
            if repair_decision.allowed:
                return TryOnQualityDecision(
                    action="repair",
                    reasons=["quality_verifier_recommended_local_repair"],
                )
            return TryOnQualityDecision(
                action="reject",
                reasons=["repair_policy_blocked", *repair_decision.rejection_reasons],
            )

        reject_reasons = self._identity_or_subject_reject_reasons(report)
        if reject_reasons:
            return TryOnQualityDecision(action="reject", reasons=reject_reasons)

        retry_categories = self._retry_categories(report)
        if retry_categories:
            return TryOnQualityDecision(
                action="retry_recommended",
                reasons=["blocking_generation_artifact"],
                retry_categories=retry_categories,
            )
        return TryOnQualityDecision(action="reject", reasons=["quality_verifier_rejected_result"])

    @staticmethod
    def _identity_or_subject_reject_reasons(report: TryOnQualityReport) -> list[str]:
        """Return hard rejection reasons when the generated person changed."""

        failed_names = {check.name.lower() for check in report.checks if check.status == "failed"}
        if failed_names.intersection(_REJECT_CHECK_NAMES):
            return ["identity_or_core_subject_changed"]
        return []

    @staticmethod
    def _retry_categories(report: TryOnQualityReport) -> list[str]:
        """Extract retry categories from blocking visual generation defects."""

        categories: set[str] = set()
        for check in report.checks:
            if check.status != "failed":
                continue
            text = f"{check.name} {check.message}".lower()
            for token, category in _RETRY_CHECK_TOKENS.items():
                if token in text:
                    categories.add(category)
        return sorted(categories)
