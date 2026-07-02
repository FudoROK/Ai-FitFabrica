"""Shared mapping helpers for Garment Identity taxonomy outputs."""

from __future__ import annotations

from dataclasses import dataclass

from src.adk_agents.garment_identity_agent.contracts import GarmentIdentityContract
from src.use_cases.garment_taxonomy.service import GarmentTaxonomyService, UnknownGarmentTaxonomyInput


@dataclass(frozen=True)
class GarmentTaxonomyMappingResult:
    """Backend-normalized taxonomy fields for persisted garment analysis."""

    wear_control_candidates: list[dict[str, object]]
    unknown_taxonomy_candidate: dict[str, object] | None


async def map_garment_taxonomy_outputs(
    *,
    job_id: str,
    output: GarmentIdentityContract,
    taxonomy_service: GarmentTaxonomyService | None,
) -> GarmentTaxonomyMappingResult:
    """Filter agent-proposed controls and capture unknown taxonomy candidates."""
    unknown_candidate = (
        output.unknown_taxonomy_candidate.model_dump(mode="json")
        if output.unknown_taxonomy_candidate is not None
        else None
    )
    if taxonomy_service is None:
        return GarmentTaxonomyMappingResult(
            wear_control_candidates=[item.model_dump(mode="json") for item in output.wear_control_candidates],
            unknown_taxonomy_candidate=unknown_candidate,
        )

    if output.unknown_taxonomy_candidate is not None:
        await taxonomy_service.resolve_available_controls(
            garment_type=output.garment_type,
            unknown_input=UnknownGarmentTaxonomyInput(
                proposed_display_name=output.unknown_taxonomy_candidate.proposed_display_name,
                proposed_category=output.unknown_taxonomy_candidate.proposed_category,
                proposed_controls=output.unknown_taxonomy_candidate.proposed_controls,
                source_job_id=job_id,
                confidence=output.unknown_taxonomy_candidate.confidence,
                agent_reasoning_summary=output.unknown_taxonomy_candidate.agent_reasoning_summary,
            ),
        )

    proposed_codes = [candidate.control_code for candidate in output.wear_control_candidates]
    approved_controls = await taxonomy_service.filter_agent_control_candidates(
        garment_type=output.garment_type,
        proposed_control_codes=proposed_codes,
    )
    approved_by_code = {control.control_code: control.control_code for control in approved_controls}
    filtered_candidates: list[dict[str, object]] = []
    for candidate in output.wear_control_candidates:
        normalized_code = _normalize_code(candidate.control_code)
        approved_code = approved_by_code.get(normalized_code)
        if approved_code is None:
            continue
        payload = candidate.model_dump(mode="json")
        payload["control_code"] = approved_code
        filtered_candidates.append(payload)

    return GarmentTaxonomyMappingResult(
        wear_control_candidates=filtered_candidates,
        unknown_taxonomy_candidate=unknown_candidate,
    )


def _normalize_code(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", " ").split())
