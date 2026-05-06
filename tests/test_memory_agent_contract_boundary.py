from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.memory.memory_agent_output_validator import MemoryAgentOutputValidator
from src.domain.memory.memory_agent_semantic_validator import (
    MemorySemanticValidationOutcome,
    MemoryAgentSemanticValidator,
)
from src.runtime_agents.memory_agent.contracts import DailyMemoryContract
from src.memory_layer.use_cases import ProcessDailyAgentOutputUseCase


def test_memory_agent_output_validator_rejects_non_canonical_legacy_payload():
    validator = MemoryAgentOutputValidator()

    with pytest.raises(ValidationError):
        validator.validate(
            payload={
                "daily_summary_text": "daily",
            }
        )


def test_memory_agent_output_validator_accepts_canonical_payload_only():
    validator = MemoryAgentOutputValidator()

    output = validator.validate(
        payload={
            "daily_summary": {
                "summary_text": "daily",
                "open_questions": ["budget"],
                "carry_forward_notes": ["return tomorrow"],
                "learned_facts": ["budget under review"],
                "changed_facts": [],
                "memory_relevance_flags": [],
            },
        }
    )

    assert output.daily_summary.summary_text == "daily"


def test_memory_agent_output_validator_accepts_semantic_null_lists_by_normalizing_them():
    validator = MemoryAgentOutputValidator()

    with pytest.raises(ValidationError):
        validator.validate(
            payload={
                "daily_summary": {
                    "summary_text": "daily",
                    "open_questions": None,
                    "carry_forward_notes": None,
                    "learned_facts": None,
                    "changed_facts": None,
                },
            }
        )


def test_memory_agent_semantic_validator_rejects_raw_message_markers():
    validator = MemoryAgentOutputValidator()
    semantic_validator = MemoryAgentSemanticValidator()

    output = validator.validate(
        payload={
            "daily_summary": {
                "summary_text": "daily",
                "open_questions": [],
                "carry_forward_notes": [],
                "learned_facts": [],
                "changed_facts": [],
                "memory_relevance_flags": [],
            },
            "active_window_update": {"memory_relevance_flags": ["messages"]},
        }
    )
    result = semantic_validator.validate(output=output)

    assert result.outcome == MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT
    assert "active_window_raw_message_marker" in result.violation_codes


def test_process_memory_agent_output_use_case_soft_rejects_semantically_invalid_output():
    use_case = ProcessDailyAgentOutputUseCase()

    result = use_case.execute(
        payload=DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        )
    )

    assert result.accepted is False
    assert result.output is not None
    assert result.error_code == "domain_semantic_invalid"
    assert result.retryable is False
    assert "daily_summary_empty" in result.semantic_result.violation_codes


def test_process_memory_agent_output_use_case_accepts_valid_daily_summary_content():
    use_case = ProcessDailyAgentOutputUseCase()

    result = use_case.execute(
        payload=DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "Клиент уточнил сроки и бюджет, ждём подтверждение по договору.",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        )
    )

    assert result.accepted is True
    assert result.error_code is None


def test_process_memory_agent_output_use_case_marks_contract_invalid_for_schema_errors():
    with pytest.raises(ValidationError):
        DailyMemoryContract.model_validate({"active_window_update": "invalid"})


def test_process_memory_agent_output_use_case_rejects_non_canonical_payload_when_adapter_disabled():
    use_case = ProcessDailyAgentOutputUseCase()

    result = use_case.execute(
        payload=DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        )
    )

    assert result.accepted is False
    assert result.output is not None
    assert result.error_code == "domain_semantic_invalid"


def test_process_memory_agent_output_use_case_accepts_contract_v2_canonical_payload():
    use_case = ProcessDailyAgentOutputUseCase()
    result = use_case.execute(
        payload=DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "contract-v2",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        )
    )
    assert result.accepted is True
    assert result.output is not None
    assert result.output.daily_summary.summary_text == "contract-v2"


def test_process_memory_agent_output_requires_reason_code_for_explicit_fallback():
    use_case = ProcessDailyAgentOutputUseCase()
    result = use_case.execute(
        payload=DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        ),
        profile_enabled=False,
    )
    assert result.accepted is False
    assert result.error_code == "domain_semantic_invalid"


def test_process_memory_agent_output_requires_emergency_reason_code():
    use_case = ProcessDailyAgentOutputUseCase()
    result = use_case.execute(
        payload=DailyMemoryContract.model_validate(
            {
                "daily_summary": {
                    "summary_text": "",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        ),
        profile_enabled=False,
    )
    assert result.accepted is False
    assert result.error_code == "domain_semantic_invalid"
