"""Backend-owned continuation policy for Garment Identity analysis."""

from __future__ import annotations

from src.domain.garment_identity import GarmentIdentityPolicyDecision, GarmentIdentityVerdict, GarmentIdentityWorkflowMode


class GarmentIdentityContinuationPolicy:
    """Decide whether validated garment analysis is suitable for workflow continuation."""

    def __init__(self, *, minimum_confidence: float) -> None:
        """Store the configured fail-closed confidence threshold."""

        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self._minimum_confidence = minimum_confidence

    def evaluate(
        self,
        *,
        workflow_mode: GarmentIdentityWorkflowMode,
        garment_count: int,
        garment_visibility: str,
        crop_quality: str,
        try_on_garment_coverage: str,
        product_card_coverage: str,
        occlusion_risk: str,
        required_regions_missing: list[str],
        ambiguous_target: bool,
        confidence: float,
        uncertainty_level: str,
    ) -> GarmentIdentityPolicyDecision:
        """Return a deterministic backend verdict for one validated analysis."""

        reasons: list[str] = []
        if garment_count == 0:
            reasons.append("no_garment_detected")
        if garment_count > 1:
            reasons.append("multiple_garments_detected")
            if ambiguous_target:
                reasons.append("ambiguous_target_garment")
        if garment_visibility == "not_visible":
            reasons.append("garment_not_visible")
        if garment_visibility == "partially_visible":
            reasons.append("garment_not_sufficiently_visible")
        if crop_quality in {"major_crop", "extreme_crop"}:
            reasons.append("garment_crop_too_tight")
        if workflow_mode == GarmentIdentityWorkflowMode.TRY_ON and try_on_garment_coverage != "sufficient":
            reasons.append("insufficient_try_on_garment_coverage")
        if workflow_mode == GarmentIdentityWorkflowMode.PRODUCT_CARD and product_card_coverage != "sufficient":
            reasons.append("insufficient_product_card_coverage")
        if occlusion_risk == "high":
            reasons.append("garment_occlusion_risk_too_high")
        if required_regions_missing:
            reasons.append("required_garment_regions_missing")
        if confidence < self._minimum_confidence:
            reasons.append("confidence_below_minimum")
        if uncertainty_level == "high":
            reasons.append("uncertainty_too_high")
        return GarmentIdentityPolicyDecision(
            verdict=GarmentIdentityVerdict.BLOCKED if reasons else GarmentIdentityVerdict.ALLOWED,
            rejection_reasons=reasons,
        )
