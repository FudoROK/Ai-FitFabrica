
from .profile import build_crm_profile_from_lead


def derive_lead_state_flags(non_empty_patch: dict[str, object]) -> dict[str, object]:
    """Derive lightweight state flags from the minimal skeleton lead patch."""

    updates: dict[str, object] = {}
    if non_empty_patch.get("first_name"):
        updates["has_name"] = True
    return updates


__all__ = ["build_crm_profile_from_lead", "derive_lead_state_flags"]
