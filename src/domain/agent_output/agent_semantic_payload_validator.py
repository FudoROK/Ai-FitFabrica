from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class SemanticValidationOutcome(StrEnum):
    SEMANTIC_OK = "semantic_ok"
    SEMANTIC_REJECT_SOFT = "semantic_reject_soft"
    SEMANTIC_REJECT_HARD = "semantic_reject_hard"


@dataclass(frozen=True)
class SemanticValidationResult:
    outcome: SemanticValidationOutcome
    violation_codes: tuple[str, ...] = ()
    observation_codes: tuple[str, ...] = ()


class SystemPayloadSemanticValidator:
    """Semantic gate for system_payload business-meaning constraints."""

    _BLOCKING_RULE_CODES: frozenset[str] = frozenset(
        {
            "canonical_location_in_memory",
            "canonical_profile_slot_misuse",
            "routing_decision_invalid_selected_agent",
            "timezone_without_backend_resolution_path",
        }
    )
    _NON_BLOCKING_RULE_CODES: frozenset[str] = frozenset({"routing_decision_unexpected_agent"})
    _CANONICAL_IN_MEMORY_MARKERS: tuple[str, ...] = (
        "first name",
        "full name",
        "business type",
        "business description",
        "budget",
    )
    _CANONICAL_SLOT_BY_MARKER: dict[str, tuple[str, ...]] = {
        "first name": ("first_name", "name", "full_name"),
        "full name": ("full_name", "name"),
        "business type": ("business_type",),
        "business description": ("business_description",),
        "budget": ("budget",),
    }

    def validate(self, *, system_payload: Any) -> SemanticValidationResult:
        logger.info("semantic_validation_started")

        payload = system_payload if isinstance(system_payload, dict) else {}
        rule_hits = (
            *self._check_canonical_location_misuse(payload),
            *self._check_timezone_semantics(payload),
            *self._check_slot_misuse(payload),
            *self._check_routing_misuse(payload),
        )

        violation_codes = tuple(code for code in rule_hits if code in self._BLOCKING_RULE_CODES)
        observation_codes = tuple(code for code in rule_hits if code in self._NON_BLOCKING_RULE_CODES)

        if violation_codes:
            logger.warning(
                "semantic_contract_violation",
                extra={
                    "violation_codes": list(violation_codes),
                    "observation_codes": list(observation_codes),
                },
            )
            return SemanticValidationResult(
                outcome=SemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                violation_codes=violation_codes,
                observation_codes=observation_codes,
            )

        if observation_codes:
            logger.info("semantic_contract_observation", extra={"observation_codes": list(observation_codes)})

        logger.info("semantic_validation_passed")
        return SemanticValidationResult(
            outcome=SemanticValidationOutcome.SEMANTIC_OK,
            observation_codes=observation_codes,
        )

    def _check_canonical_location_misuse(self, payload: dict[str, Any]) -> tuple[str, ...]:
        memory_patch = payload.get("memory_patch")
        if not isinstance(memory_patch, dict):
            return ()

        lead_patch = payload.get("lead_patch")
        lead_city = lead_patch.get("city") if isinstance(lead_patch, dict) else None
        lead_country = lead_patch.get("country") if isinstance(lead_patch, dict) else None

        facts = memory_patch.get("important_facts_add")
        if not isinstance(facts, list):
            return ()

        normalized_facts = [str(item).strip().lower() for item in facts if isinstance(item, str)]
        city_in_memory = any("city" in fact for fact in normalized_facts)
        country_in_memory = any("country" in fact for fact in normalized_facts)
        if (city_in_memory and not lead_city) or (country_in_memory and not lead_country):
            return ("canonical_location_in_memory",)
        return ()

    def _check_timezone_semantics(self, payload: dict[str, Any]) -> tuple[str, ...]:
        lead_patch = payload.get("lead_patch")
        if not isinstance(lead_patch, dict):
            return ()

        timezone_value = lead_patch.get("timezone")
        city_value = lead_patch.get("city")
        country_value = lead_patch.get("country")

        if isinstance(timezone_value, str) and timezone_value.strip() and not (city_value or country_value):
            return ("timezone_without_backend_resolution_path",)
        return ()

    def _check_slot_misuse(self, payload: dict[str, Any]) -> tuple[str, ...]:
        memory_patch = payload.get("memory_patch")
        if not isinstance(memory_patch, dict):
            return ()

        facts = memory_patch.get("important_facts_add")
        if not isinstance(facts, list):
            return ()

        lead_patch = payload.get("lead_patch")
        canonical_slots = lead_patch if isinstance(lead_patch, dict) else {}

        normalized_facts = [str(item).strip().lower() for item in facts if isinstance(item, str)]
        for marker in self._CANONICAL_IN_MEMORY_MARKERS:
            if not any(marker in fact for fact in normalized_facts):
                continue
            canonical_keys = self._CANONICAL_SLOT_BY_MARKER.get(marker, ())
            if any(canonical_slots.get(key) for key in canonical_keys):
                continue
            if any("lead_profile" in fact for fact in normalized_facts):
                return ("canonical_profile_slot_misuse",)
        return ()

    def _check_routing_misuse(self, payload: dict[str, Any]) -> tuple[str, ...]:
        routing_decision = payload.get("routing_decision")
        if not isinstance(routing_decision, dict):
            return ()

        selected_agent = routing_decision.get("selected_agent")
        if selected_agent is None:
            return ()

        if not isinstance(selected_agent, str) or not selected_agent.strip():
            return ("routing_decision_invalid_selected_agent",)

        known_agents = {
            "primary_agent",
            "support",
            "qualification",
            "default",
            "ai_solution_primary_agent",
            "leadqualificationagent",
        }
        if selected_agent.strip().lower() not in known_agents:
            return ("routing_decision_unexpected_agent",)

        return ()
