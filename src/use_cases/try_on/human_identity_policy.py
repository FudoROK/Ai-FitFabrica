"""Backend-owned continuation policy for Human Identity analysis."""

from __future__ import annotations

from src.domain.try_on import TryOnHumanIdentityPolicyDecision, TryOnHumanIdentityVerdict


class HumanIdentityContinuationPolicy:
    """Decide whether validated human analysis is suitable for generation."""

    def __init__(self, *, minimum_confidence: float) -> None:
        """Store the configured fail-closed confidence threshold."""

        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self._minimum_confidence = minimum_confidence

    def evaluate(
        self,
        *,
        face_visibility: str,
        body_region_visibility: list[str],
        preservation_target_count: int,
        confidence: float,
        uncertainty_level: str,
        subject_count: int,
        crop_quality: str,
        try_on_body_coverage: str,
        occlusion_risk: str,
        required_regions_missing: list[str],
    ) -> TryOnHumanIdentityPolicyDecision:
        """Return a deterministic backend verdict for one validated analysis."""

        reasons: list[str] = []
        if subject_count == 0:
            reasons.append("no_human_subject_detected")
        if subject_count > 1:
            reasons.append("multiple_subjects_detected")
        if face_visibility == "not_visible":
            reasons.append("face_not_visible")
        if face_visibility != "fully_visible":
            reasons.append("face_not_fully_visible")
        if not body_region_visibility:
            reasons.append("body_regions_not_visible")
        if crop_quality in {"headshot", "extreme_crop"}:
            reasons.append("tight_headshot_crop")
        if try_on_body_coverage == "insufficient":
            reasons.append("insufficient_body_coverage")
        if occlusion_risk == "high":
            reasons.append("human_occlusion_risk_too_high")
        if required_regions_missing:
            reasons.append("required_regions_missing")
        if confidence < self._minimum_confidence:
            reasons.append("confidence_below_minimum")
        if uncertainty_level == "high":
            reasons.append("uncertainty_too_high")
        return TryOnHumanIdentityPolicyDecision(
            verdict=TryOnHumanIdentityVerdict.BLOCKED if reasons else TryOnHumanIdentityVerdict.ALLOWED,
            rejection_reasons=reasons,
        )
