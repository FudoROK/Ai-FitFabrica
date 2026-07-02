"""Backend-owned policy helpers for garment taxonomy controls."""

from __future__ import annotations

from src.domain.garment_taxonomy import GarmentWearControl


def choose_auto_control(controls: list[GarmentWearControl]) -> GarmentWearControl:
    """Choose the deterministic backend default for auto mode."""
    for control in controls:
        if control.default_for_auto:
            return control
    if not controls:
        raise ValueError("no available wear controls for auto mode")
    return controls[0]


def filter_allowed_controls(
    *,
    controls: list[GarmentWearControl],
    proposed_control_codes: list[str],
) -> list[GarmentWearControl]:
    """Return proposed controls that exist in the approved backend catalog."""
    requested = {_normalize_candidate_code(code) for code in proposed_control_codes if code.strip()}
    return [control for control in controls if control.control_code in requested]


def _normalize_candidate_code(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", " ").split())

