from __future__ import annotations

import pytest

from src.domain.material_texture import MaterialTextureVerdict
from src.use_cases.material_texture_policy import MaterialTextureContinuationPolicy


def _analysis_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "visible_material_signal_count": 1,
        "texture_signal_count": 1,
        "observation_count": 1,
        "evidence_count": 1,
        "confidence": 0.86,
        "uncertainty_level": "medium",
    }
    values.update(overrides)
    return values


def test_material_texture_policy_allows_evidence_backed_visual_estimate() -> None:
    decision = MaterialTextureContinuationPolicy(minimum_confidence=0.7).evaluate(**_analysis_values())

    assert decision.verdict == MaterialTextureVerdict.ALLOWED
    assert decision.rejection_reasons == []


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        (
            {"visible_material_signal_count": 0, "texture_signal_count": 0, "observation_count": 0},
            "material_texture_visible_signals_missing",
        ),
        ({"evidence_count": 0}, "material_texture_evidence_missing"),
        ({"confidence": 0.2}, "confidence_below_minimum"),
        ({"uncertainty_level": "high"}, "uncertainty_too_high"),
    ],
)
def test_material_texture_policy_blocks_unsafe_analysis(overrides: dict[str, object], reason: str) -> None:
    decision = MaterialTextureContinuationPolicy(minimum_confidence=0.7).evaluate(**_analysis_values(**overrides))

    assert decision.verdict == MaterialTextureVerdict.BLOCKED
    assert reason in decision.rejection_reasons
