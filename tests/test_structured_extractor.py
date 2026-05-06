from __future__ import annotations

from src.llm.transport.structured_extractor import collect_raw_structured_payload_candidates, extract_raw_structured_payload


def test_extractor_reads_function_call_args_payload():
    payload = {"x": 1}
    event = {"content": {"parts": [{"function_call": {"name": "handoff", "args": payload}}]}}

    assert extract_raw_structured_payload(event) == payload


def test_extractor_reads_function_call_arguments_payload():
    payload = {"x": 2}
    event = {"content": {"parts": [{"function_call": {"name": "handoff", "arguments": payload}}]}}

    assert extract_raw_structured_payload(event) == payload


def test_extractor_reads_functionCall_args_payload():
    payload = {"y": 1}
    event = {"content": {"parts": [{"functionCall": {"name": "handoff", "args": payload}}]}}

    assert extract_raw_structured_payload(event) == payload


def test_extractor_reads_functionCall_arguments_payload():
    payload = {"y": 2}
    event = {"content": {"parts": [{"functionCall": {"name": "handoff", "arguments": payload}}]}}

    assert extract_raw_structured_payload(event) == payload


def test_extractor_returns_none_when_payload_missing():
    assert extract_raw_structured_payload({"content": "plain text"}) is None


def test_extractor_does_not_parse_json_from_text_payload():
    event = {"content": '{"reply_text":"rescued","system_payload":{}}'}

    assert extract_raw_structured_payload(event) is None


def test_extractor_returns_raw_dict_without_domain_typing():
    payload = {"unexpected": {"nested": True}, "meta": ["a"]}
    event = {"output": payload}

    extracted = extract_raw_structured_payload(event)

    assert extracted == payload
    assert isinstance(extracted, dict)
    assert "reply_text" not in extracted


def test_extractor_collects_candidates_with_path_event_index_and_depth():
    payload = {"reply_text": "ok", "system_payload": {}}
    event = {"content": {"parts": [{"function_call": {"arguments": payload}}]}}

    candidates = collect_raw_structured_payload_candidates(event, event_index=3)

    assert len(candidates) == 4
    assert candidates[-1]["payload"] == payload
    assert candidates[-1]["event_index"] == 3
    assert candidates[-1]["path"].endswith("function_call.arguments")
    assert candidates[-1]["depth"] > 0
