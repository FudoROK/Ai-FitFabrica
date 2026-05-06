from __future__ import annotations

import pytest

from src.llm.core.result import LLMResult as CoreLLMResult
from src.runtime_agents.memory_agent.memory_response_parser import parse_provider_response


def _result(payload: dict) -> CoreLLMResult:
    return CoreLLMResult(status="ok", structured_data=payload, provider="vertex")


def _canonical_rolling_update(
    summary_text: str = "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.",
) -> dict[str, object]:
    return {
        "rolling_summary_text": summary_text,
        "open_questions": [],
        "carry_forward_notes": [],
        "days_count": 1,
        "last_daily_summary_date": "2025-01-01",
        "version": 1,
    }


def test_memory_parser_accepts_valid_runtime_contract_payload() -> None:
    parsed = parse_provider_response(
        _result(
            {
                "active_window_update": {"open_topics": ["budget"]},
                "daily_summary": {
                    "summary_text": "Lead clarified budget and timeline.",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
                "conversation_state_update": {"current_stage": "qualification"},
            }
        )
    )

    assert parsed["daily_summary"]["summary_text"].startswith("Lead clarified")


def test_memory_parser_rejects_rolling_payload_for_daily_parser() -> None:
    with pytest.raises(ValueError, match="daily_contract_invalid"):
        parse_provider_response(
            _result(
                {
                    "rolling_update": _canonical_rolling_update(),
                }
            )
        )


def test_memory_parser_accepts_nullable_optional_top_level_blocks_only() -> None:
    parsed = parse_provider_response(
        _result(
            {
                "active_window_update": None,
                "daily_summary": {
                    "summary_text": "No significant new durable facts today.",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
                "conversation_state_update": None,
            }
        )
    )

    assert parsed["daily_summary"]["summary_text"] == "No significant new durable facts today."


def test_memory_parser_rejects_extra_top_level_keys() -> None:
    with pytest.raises(ValueError, match="daily_contract_invalid"):
        parse_provider_response(
            _result(
                {
                    "active_window_update": None,
                    "daily_summary": {"summary_text": "ok"},
                    "conversation_state_update": None,
                    "unexpected": "forbidden",
                }
            )
        )


def test_memory_parser_accepts_missing_optional_top_level_keys() -> None:
    parsed = parse_provider_response(
        _result(
            {
                "daily_summary": {
                    "summary_text": "ok",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
            }
        )
    )

    assert parsed["daily_summary"]["summary_text"] == "ok"
    assert "active_window_update" not in parsed
    assert "conversation_state_update" not in parsed


def test_memory_parser_rejects_type_mismatch() -> None:
    with pytest.raises(ValueError, match="daily_contract_invalid"):
        parse_provider_response(
            _result(
                {
                    "active_window_update": None,
                    "daily_summary": {
                        "summary_text": "ok",
                        "open_questions": [],
                        "carry_forward_notes": [],
                        "learned_facts": [],
                        "changed_facts": [],
                        "memory_relevance_flags": "not-a-list",
                    },
                    "conversation_state_update": None,
                }
            )
        )

def test_memory_parser_does_not_mutate_missing_content_fields() -> None:
    parsed = parse_provider_response(
        _result(
            {
                "daily_summary": {
                    "summary_text": "Lead provided no new updates.",
                    "open_questions": [],
                    "carry_forward_notes": [],
                    "learned_facts": [],
                    "changed_facts": [],
                    "memory_relevance_flags": [],
                },
                "conversation_state_update": {
                    "open_questions": [],
                    "answered_topics": [],
                },
            }
        )
    )

    assert "meta_trace" not in parsed
    assert "active_window_update" not in parsed
    assert parsed["conversation_state_update"]["answered_topics"] == []
