"""Shared garment category normalization rules."""

from __future__ import annotations


def canonicalize_garment_category(value: str | None) -> str | None:
    """Map product and agent garment labels to stable catalog category keys."""

    normalized = (value or "").strip().casefold().replace("_", " ").replace("-", " ")
    if not normalized:
        return None
    if any(token in normalized for token in ("jacket", "coat", "blazer", "outerwear", "puffer", "quilted")):
        return "outerwear"
    if any(token in normalized for token in ("tshirt", "t shirt", "tee", "longsleeve", "long sleeve")):
        return "tshirt"
    if any(token in normalized for token in ("shirt", "button up", "buttondown", "button down", "blouse")):
        return "shirt"
    if any(token in normalized for token in ("pants", "trouser", "jeans", "denim", "cargo", "palazzo")):
        return "pants"
    if "dress" in normalized:
        return "dress"
    if "skirt" in normalized:
        return "skirt"
    return normalized
