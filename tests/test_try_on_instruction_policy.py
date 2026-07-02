from __future__ import annotations

import pytest

from src.domain.try_on_instruction import TryOnInstructionVerdict
from src.use_cases.try_on.instruction_policy import TryOnInstructionContinuationPolicy


def _instruction_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "preserve_face": True,
        "preserve_body_shape": True,
        "preserve_pose": True,
        "garment_focus_point_count": 1,
        "generation_exclusion_count": 1,
        "evidence_count": 1,
        "confidence": 0.91,
        "uncertainty_level": "low",
    }
    values.update(overrides)
    return values


def test_try_on_instruction_policy_allows_safe_instruction() -> None:
    decision = TryOnInstructionContinuationPolicy(minimum_confidence=0.8).evaluate(**_instruction_values())

    assert decision.verdict == TryOnInstructionVerdict.ALLOWED
    assert decision.rejection_reasons == []


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"preserve_face": False}, "preserve_face_disabled"),
        ({"preserve_body_shape": False}, "preserve_body_shape_disabled"),
        ({"preserve_pose": False}, "preserve_pose_disabled"),
        ({"garment_focus_point_count": 0}, "garment_focus_points_missing"),
        ({"generation_exclusion_count": 0}, "generation_exclusions_missing"),
        ({"evidence_count": 0}, "instruction_evidence_missing"),
        ({"confidence": 0.4}, "confidence_below_minimum"),
        ({"uncertainty_level": "high"}, "uncertainty_too_high"),
    ],
)
def test_try_on_instruction_policy_blocks_unsafe_instruction(overrides: dict[str, object], reason: str) -> None:
    decision = TryOnInstructionContinuationPolicy(minimum_confidence=0.8).evaluate(**_instruction_values(**overrides))

    assert decision.verdict == TryOnInstructionVerdict.BLOCKED
    assert reason in decision.rejection_reasons
