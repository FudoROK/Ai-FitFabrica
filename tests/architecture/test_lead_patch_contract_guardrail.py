from __future__ import annotations

from typing import Iterable

from src.domain.extraction import CANONICAL_PATCH_KEYS, LEAD_PATCH_SUPPORTED_FIELDS
from src.llm.vertex.vertex_schema_validator import AGENT_OUTPUT_SCHEMA
from src.llm.tasks.primary_agent.profile_extract_task import LeadPatch, lead_profile_schema


def _as_sorted_tuple(fields: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(fields))


def _assert_same_fields(*, source_name: str, expected: Iterable[str], actual_name: str, actual: Iterable[str]) -> None:
    expected_set = set(expected)
    actual_set = set(actual)
    missing = _as_sorted_tuple(expected_set - actual_set)
    extra = _as_sorted_tuple(actual_set - expected_set)

    assert expected_set == actual_set, (
        f"{source_name} != {actual_name}. "
        f"{source_name}: {_as_sorted_tuple(expected_set)}; "
        f"{actual_name}: {_as_sorted_tuple(actual_set)}; "
        f"missing: {missing}; "
        f"extra: {extra}"
    )


def test_lead_patch_contract_is_consistent_across_canonical_model_and_schemas() -> None:
    canonical_fields = tuple(CANONICAL_PATCH_KEYS)
    supported_fields = tuple(LEAD_PATCH_SUPPORTED_FIELDS)

    _assert_same_fields(
        source_name="CANONICAL_PATCH_KEYS",
        expected=canonical_fields,
        actual_name="LEAD_PATCH_SUPPORTED_FIELDS",
        actual=supported_fields,
    )

    lead_patch_model_fields = tuple(LeadPatch.model_fields.keys())
    _assert_same_fields(
        source_name="CANONICAL_PATCH_KEYS",
        expected=canonical_fields,
        actual_name="LeadPatch.model_fields",
        actual=lead_patch_model_fields,
    )

    schema = lead_profile_schema()
    lead_patch_schema = schema["properties"]["lead_patch"]
    lead_patch_schema_properties = tuple(lead_patch_schema["properties"].keys())
    lead_patch_schema_required = tuple(lead_patch_schema["required"])

    _assert_same_fields(
        source_name="CANONICAL_PATCH_KEYS",
        expected=canonical_fields,
        actual_name="lead_profile_schema.lead_patch.properties",
        actual=lead_patch_schema_properties,
    )
    _assert_same_fields(
        source_name="lead_profile_schema.lead_patch.properties",
        expected=lead_patch_schema_properties,
        actual_name="lead_profile_schema.lead_patch.required",
        actual=lead_patch_schema_required,
    )

    # primary_agent output is intentionally narrower than profile_extract:
    # skeleton runtime only extracts explicit first_name from live dialogue.
    vertex_lead_patch_schema = AGENT_OUTPUT_SCHEMA["properties"]["system_payload"]["properties"]["lead_patch"]
    vertex_lead_patch_properties = tuple(vertex_lead_patch_schema["properties"].keys())

    assert vertex_lead_patch_properties == ("first_name",)
