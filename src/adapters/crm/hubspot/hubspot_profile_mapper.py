from __future__ import annotations

def build_hubspot_profile_from_lead(lead) -> dict[str, str]:
    raise RuntimeError(
        "build_hubspot_profile_from_lead is deprecated; "
        "use src.domain.crm.profile.build_crm_profile_from_lead and src.adapters.crm.hubspot.hubspot_mapper.build_contact_properties"
    )


def derive_lead_state_flags(non_empty_patch: dict[str, object]) -> dict[str, object]:
    updates: dict[str, object] = {}
    if non_empty_patch.get("first_name"):
        updates["has_name"] = True
    if non_empty_patch.get("business_type"):
        updates["has_business"] = True
    if non_empty_patch.get("pain_points"):
        updates["has_pains"] = True
    if non_empty_patch.get("needs") or non_empty_patch.get("recommended_package"):
        updates["has_needs"] = True
    return updates
