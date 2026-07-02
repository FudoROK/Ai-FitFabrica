"""Deterministic policy for valid multi-garment Try-On slot combinations."""

from __future__ import annotations

from src.domain.try_on import TryOnUploadRole
from src.domain.try_on_outfit import TryOnOutfitCompositionDecision, TryOnOutfitCompositionVerdict

_GARMENT_ROLES = {
    TryOnUploadRole.GARMENT_PHOTO,
    TryOnUploadRole.UPPER_GARMENT_PHOTO,
    TryOnUploadRole.LOWER_GARMENT_PHOTO,
    TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO,
    TryOnUploadRole.FULL_BODY_GARMENT_PHOTO,
}


def evaluate_outfit_composition(roles: list[TryOnUploadRole]) -> TryOnOutfitCompositionVerdict:
    """Return a fail-closed verdict for one requested outfit slot combination."""
    garment_roles = [role for role in roles if role in _GARMENT_ROLES]
    reasons: list[str] = []
    warnings: list[str] = []
    role_set = set(garment_roles)

    if len(role_set) != len(garment_roles):
        reasons.append("duplicate_garment_slot")

    if TryOnUploadRole.GARMENT_PHOTO in role_set and len(role_set) > 1:
        reasons.append("legacy_garment_conflicts_with_outfit_slots")

    if TryOnUploadRole.FULL_BODY_GARMENT_PHOTO in role_set and len(role_set) > 1:
        reasons.append("full_body_conflicts_with_separate_slots")

    if TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO in role_set and not {
        TryOnUploadRole.UPPER_GARMENT_PHOTO,
        TryOnUploadRole.LOWER_GARMENT_PHOTO,
    }.issubset(role_set):
        reasons.append("base_outfit_required_for_outerwear")

    if TryOnUploadRole.LOWER_GARMENT_PHOTO in role_set and TryOnUploadRole.UPPER_GARMENT_PHOTO not in role_set:
        reasons.append("upper_garment_required_for_lower_slot")

    if not role_set:
        reasons.append("garment_slot_required")

    if reasons:
        return TryOnOutfitCompositionVerdict(
            decision=TryOnOutfitCompositionDecision.BLOCK,
            reasons=sorted(set(reasons)),
            warnings=warnings,
        )
    return TryOnOutfitCompositionVerdict(
        decision=TryOnOutfitCompositionDecision.ALLOW,
        reasons=[],
        warnings=warnings,
    )
