from __future__ import annotations

import pytest

from src.llm.contract_kinds import REPLY_AGENT_OUTPUT_KIND, canonicalize_contract_kind
from src.llm.vertex.vertex_parser import (
    collect_output_from_events,
    get_contract_selector,
    resolve_contract_selector,
)
from src.llm.vertex.vertex_parser_selectors import selector_mode_name


def test_collect_output_from_events_accepts_output_dict_payload():
    payload = {"reply_text": "ok", "system_payload": {}}

    parsed = collect_output_from_events([{"output": payload}], contract_kind=REPLY_AGENT_OUTPUT_KIND)

    assert parsed["output"] == payload
    assert parsed["event_count"] == 1


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


def test_resolve_contract_selector_uses_reply_selector():
    selector = resolve_contract_selector(contract_kind=REPLY_AGENT_OUTPUT_KIND)

    assert callable(selector)


def test_reply_selector_mode_name_is_stable():
    assert selector_mode_name(contract_kind=REPLY_AGENT_OUTPUT_KIND) == "reply_envelope_contract"


def test_collect_output_from_events_rejects_unknown_contract_kind_without_reply_fallback():
    with pytest.raises(ValueError, match="unknown contract_kind"):
        collect_output_from_events([{"output": {"reply_text": "ok", "system_payload": {}}}], contract_kind="bad_kind")


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
