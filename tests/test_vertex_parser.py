from __future__ import annotations

import pytest

from src.llm.contract_kinds import (
    MEMORY_DAILY_OUTPUT_KIND,
    MEMORY_ROLLING_OUTPUT_KIND,
    REPLY_AGENT_OUTPUT_KIND,
    canonicalize_contract_kind,
)
from src.llm.vertex.vertex_parser import (
    collect_output_from_events,
    get_contract_selector,
    resolve_contract_selector,
    select_canonical_daily_memory_output_candidate,
    select_canonical_rolling_memory_output_candidate,
    selector_mode_name,
)


def _daily_payload(summary_text: str = "ready") -> dict:
    return {
        "daily_summary": {
            "summary_text": summary_text,
            "open_questions": [],
            "carry_forward_notes": [],
            "learned_facts": [],
            "changed_facts": [],
            "memory_relevance_flags": [],
        },
        "active_window_update": {
            "open_topics": [],
            "local_context_text": None,
            "memory_relevance_flags": [],
        },
        "conversation_state_update": {
            "current_stage": "qualification",
            "open_questions": [],
            "answered_topics": [],
        },
    }


def _rolling_payload(summary_text: str = "rolling") -> dict:
    return {
        "rolling_update": {
            "rolling_summary_text": summary_text,
            "open_questions": [],
            "carry_forward_notes": [],
            "days_count": 1,
            "last_daily_summary_date": "2025-01-01",
            "version": 1,
        }
    }


def test_collect_output_from_events_accepts_output_dict_payload():
    payload = {"reply_text": "ok", "system_payload": {}}

    parsed = collect_output_from_events([{"output": payload}], contract_kind=REPLY_AGENT_OUTPUT_KIND)

    assert parsed["output"] == payload
    assert parsed["event_count"] == 1


def test_daily_memory_selector_accepts_canonical_payload_without_root_flags():
    payload = _daily_payload()

    parsed = collect_output_from_events([{"output": payload}], contract_kind=MEMORY_DAILY_OUTPUT_KIND)

    assert parsed["output"] == payload


def test_daily_memory_selector_rejects_reply_envelope_shape():
    reply_payload = {"reply_text": "ok", "system_payload": {}}

    with pytest.raises(ValueError, match="daily_contract_invalid: no valid structured candidate"):
        collect_output_from_events([{"output": reply_payload}], contract_kind=MEMORY_DAILY_OUTPUT_KIND)


def test_rolling_memory_selector_accepts_canonical_payload():
    payload = _rolling_payload("Client confirmed next steps")

    parsed = collect_output_from_events([{"output": payload}], contract_kind=MEMORY_ROLLING_OUTPUT_KIND)

    assert parsed["output"] == payload


def test_get_contract_selector_uses_daily_selector_for_daily_contract_kind():
    selector = get_contract_selector(MEMORY_DAILY_OUTPUT_KIND)
    candidate = {"payload": _daily_payload(), "path": "event.output", "depth": 1}

    assert selector(candidate)["is_valid"] is True


def test_get_contract_selector_uses_rolling_selector_for_rolling_contract_kind():
    selector = get_contract_selector(MEMORY_ROLLING_OUTPUT_KIND)
    candidate = {"payload": _rolling_payload(), "path": "event.output", "depth": 1}

    assert selector(candidate)["is_valid"] is True


def test_get_contract_selector_uses_reply_selector_for_reply_contract_kind():
    selector = get_contract_selector(REPLY_AGENT_OUTPUT_KIND)
    candidate = {"payload": {"reply_text": "ok", "system_payload": {}}, "path": "event.output", "depth": 1}

    assert selector(candidate)["is_valid"] is True


def test_get_contract_selector_rejects_unknown_contract_kind():
    with pytest.raises(ValueError, match="unknown contract_kind"):
        get_contract_selector("unknown_contract")


def test_legacy_memory_agent_output_kind_is_not_supported_anymore():
    with pytest.raises(ValueError, match="unknown contract_kind"):
        canonicalize_contract_kind("MemoryAgentOutput")


def test_resolve_contract_selector_uses_canonical_daily_memory_selector():
    selector = resolve_contract_selector(contract_kind=MEMORY_DAILY_OUTPUT_KIND)

    assert selector is select_canonical_daily_memory_output_candidate


def test_resolve_contract_selector_uses_canonical_rolling_memory_selector():
    selector = resolve_contract_selector(contract_kind=MEMORY_ROLLING_OUTPUT_KIND)

    assert selector is select_canonical_rolling_memory_output_candidate


def test_memory_selector_mode_names_are_stable():
    assert selector_mode_name(contract_kind=MEMORY_DAILY_OUTPUT_KIND) == "memory_daily_contract_boundary_v1"
    assert selector_mode_name(contract_kind=MEMORY_ROLLING_OUTPUT_KIND) == "memory_rolling_contract_boundary_v1"


def test_collect_output_from_events_rejects_unknown_contract_kind_without_reply_fallback():
    with pytest.raises(ValueError, match="unknown contract_kind"):
        collect_output_from_events([{"output": {"reply_text": "ok", "system_payload": {}}}], contract_kind="bad_kind")


def test_memory_text_fallback_accepts_daily_payload_without_root_final_semantics():
    parsed = collect_output_from_events(
        [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                '{"daily_summary":{"summary_text":"ready","open_questions":[],"carry_forward_notes":[],"learned_facts":[],"changed_facts":[],"memory_relevance_flags":[]},'
                                '"active_window_update":{"open_topics":[],"local_context_text":null,"memory_relevance_flags":[]},'
                                '"conversation_state_update":{"current_stage":"qualification","open_questions":[],"answered_topics":[]}}'
                            )
                        }
                    ]
                }
            }
        ],
        contract_kind=MEMORY_DAILY_OUTPUT_KIND,
    )

    assert parsed["output"]["daily_summary"]["summary_text"] == "ready"
    assert parsed["event_count"] == 1


def test_reply_text_fallback_behavior_remains_unchanged():
    parsed = collect_output_from_events(
        [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"reply_text":"ok","system_payload":{"source":"text_fallback"}}'
                        }
                    ]
                }
            }
        ],
        contract_kind=REPLY_AGENT_OUTPUT_KIND,
    )

    assert parsed["output"] == {"reply_text": "ok", "system_payload": {"source": "text_fallback"}}
