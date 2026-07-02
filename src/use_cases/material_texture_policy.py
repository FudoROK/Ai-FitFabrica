"""Backend-owned continuation policy for Material / Texture analysis."""

from __future__ import annotations

from src.domain.material_texture import MaterialTexturePolicyDecision, MaterialTextureVerdict


class MaterialTextureContinuationPolicy:
    """Decide whether visible material analysis is honest and usable."""

    def __init__(self, *, minimum_confidence: float) -> None:
        """Store the configured fail-closed confidence threshold."""

        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self._minimum_confidence = minimum_confidence

    def evaluate(
        self,
        *,
        visible_material_signal_count: int,
        texture_signal_count: int,
        observation_count: int,
        evidence_count: int,
        confidence: float,
        uncertainty_level: str,
    ) -> MaterialTexturePolicyDecision:
        """Return a deterministic backend verdict for one validated material analysis."""

        reasons: list[str] = []
        if visible_material_signal_count == 0 and texture_signal_count == 0 and observation_count == 0:
            reasons.append("material_texture_visible_signals_missing")
        if evidence_count == 0:
            reasons.append("material_texture_evidence_missing")
        if confidence < self._minimum_confidence:
            reasons.append("confidence_below_minimum")
        if uncertainty_level == "high":
            reasons.append("uncertainty_too_high")
        return MaterialTexturePolicyDecision(
            verdict=MaterialTextureVerdict.BLOCKED if reasons else MaterialTextureVerdict.ALLOWED,
            rejection_reasons=reasons,
        )
