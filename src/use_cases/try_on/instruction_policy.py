"""Backend-owned continuation policy for Try-On generation instructions."""

from __future__ import annotations

from src.domain.try_on_instruction import TryOnInstructionPolicyDecision, TryOnInstructionVerdict


class TryOnInstructionContinuationPolicy:
    """Decide whether a generated instruction is safe for image generation."""

    def __init__(self, *, minimum_confidence: float) -> None:
        """Store the configured fail-closed confidence threshold."""

        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self._minimum_confidence = minimum_confidence

    def evaluate(
        self,
        *,
        preserve_face: bool,
        preserve_body_shape: bool,
        preserve_pose: bool,
        garment_focus_point_count: int,
        generation_exclusion_count: int,
        evidence_count: int,
        confidence: float,
        uncertainty_level: str,
    ) -> TryOnInstructionPolicyDecision:
        """Return a deterministic backend verdict for one validated instruction."""

        reasons: list[str] = []
        if not preserve_face:
            reasons.append("preserve_face_disabled")
        if not preserve_body_shape:
            reasons.append("preserve_body_shape_disabled")
        if not preserve_pose:
            reasons.append("preserve_pose_disabled")
        if garment_focus_point_count == 0:
            reasons.append("garment_focus_points_missing")
        if generation_exclusion_count == 0:
            reasons.append("generation_exclusions_missing")
        if evidence_count == 0:
            reasons.append("instruction_evidence_missing")
        if confidence < self._minimum_confidence:
            reasons.append("confidence_below_minimum")
        if uncertainty_level == "high":
            reasons.append("uncertainty_too_high")
        return TryOnInstructionPolicyDecision(
            verdict=TryOnInstructionVerdict.BLOCKED if reasons else TryOnInstructionVerdict.ALLOWED,
            rejection_reasons=reasons,
        )
