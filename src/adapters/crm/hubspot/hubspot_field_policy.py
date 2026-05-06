from __future__ import annotations

def map_domain_profile_to_hubspot_properties(profile: dict[str, str]) -> dict[str, str]:
    raise RuntimeError(
        "map_domain_profile_to_hubspot_properties is deprecated; "
        "use src.adapters.crm.hubspot.hubspot_mapper.build_contact_properties"
    )
