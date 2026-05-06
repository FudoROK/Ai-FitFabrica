from __future__ import annotations

import pytest

from src.llm.profiles.contracts import SemanticValidationContext, ValidationResult
from src.llm.profiles.memory_profile import MemoryProfile, MemoryProfileOutput
from src.runtime_agents.memory_agent.contracts import DailyMemoryContract
from src.services.runtime.feature_flags import FeatureFlags
from src.memory_layer.use_cases.process_daily_agent_output_use_case import ProcessDailyAgentOutputUseCase


def _typed_payload(summary_text: str = "typed daily") -> DailyMemoryContract:
    return DailyMemoryContract.model_validate({"daily_summary": {"summary_text": summary_text, "open_questions": [], "carry_forward_notes": [], "learned_facts": [], "changed_facts": [], "memory_relevance_flags": []}})


def test_memory_profile_parse_validate_semantic_accept_typed_payload() -> None:
    profile = MemoryProfile()
    payload = _typed_payload()

    parsed = profile.parse(payload)

    assert isinstance(parsed, MemoryProfileOutput)
    assert parsed.memory_payload is payload
    assert profile.validate(parsed) == ValidationResult.success()
    assert profile.semantic_validate(parsed, SemanticValidationContext(payload={})) == ValidationResult.success()


def test_memory_profile_parse_rejects_non_typed_payload_without_fallback() -> None:
    profile = MemoryProfile()

    with pytest.raises(TypeError):
        profile.parse({"daily_summary": {"summary_text": "daily"}})


class _RegistryStub:
    def __init__(self, profile) -> None:
        self._profile = profile

    def get_profile(self, *, flow: str):
        assert flow == "memory"
        return self._profile


class _ValidatorSpy:
    def __init__(self) -> None:
        self.payload = None

    def validate(self, *, payload):
        self.payload = payload
        if not isinstance(payload, DailyMemoryContract):
            raise AssertionError("validator must receive typed DailyMemoryContract")
        return payload


class _SemanticValidatorStub:
    def validate(self, *, output):
        from src.domain.memory.memory_agent_semantic_validator import (
            MemorySemanticValidationOutcome,
            MemorySemanticValidationResult,
        )

        return MemorySemanticValidationResult(outcome=MemorySemanticValidationOutcome.SEMANTIC_OK, violation_codes=())


def test_memory_profile_handoff_keeps_typed_payload_and_daily_summary() -> None:
    payload = _typed_payload("handoff daily")
    validator = _ValidatorSpy()
    use_case = ProcessDailyAgentOutputUseCase(
        validator=validator,
        semantic_validator=_SemanticValidatorStub(),
        profile_registry=_RegistryStub(MemoryProfile()),
        feature_flags=FeatureFlags(enable_profile_runtime=True, enable_memory_profile=True),
    )

    result = use_case.execute(payload=payload, profile_enabled=True)

    assert result.accepted is True
    assert result.error_code is None
    assert validator.payload is payload
    assert validator.payload.daily_summary.summary_text == "handoff daily"


def test_memory_profile_regression_typed_payload_does_not_degrade_or_raise_parser_contract_invalid() -> None:
    payload = _typed_payload("regression daily")
    use_case = ProcessDailyAgentOutputUseCase(
        profile_registry=_RegistryStub(MemoryProfile()),
        feature_flags=FeatureFlags(enable_profile_runtime=True, enable_memory_profile=True),
    )

    result = use_case.execute(payload=payload, profile_enabled=True)

    assert result.accepted is True
    assert result.error_code is None
    assert result.output is not None
    assert result.output.daily_summary.summary_text == "regression daily"


def test_memory_profile_use_case_rejects_non_typed_payload_with_explicit_error() -> None:
    use_case = ProcessDailyAgentOutputUseCase(
        profile_registry=_RegistryStub(MemoryProfile()),
        feature_flags=FeatureFlags(enable_profile_runtime=True, enable_memory_profile=True),
    )

    result = use_case.execute(
        payload={
            "daily_summary": {
                "summary_text": "legacy",
                "open_questions": [],
                "carry_forward_notes": [],
                "learned_facts": [],
                "changed_facts": [],
                "memory_relevance_flags": [],
            },
        },
        profile_enabled=True,
    )

    assert result.accepted is False
    assert result.error_code == "parser_contract_invalid"
    assert result.error_message == "memory_profile_parse_type_error"
