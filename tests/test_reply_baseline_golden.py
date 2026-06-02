from __future__ import annotations

import asyncio

import pytest

from src.llm.core.result import LLMResult as CoreLLMResult
from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema
from src.llm.tasks.dialog_reply_task import parse_provider_response
from src.runtime_agents.dialog_reply.dialog_reply_request_factory import build_provider_request
from src.use_cases.dialog.generate_reply_use_case import GenerateReplyUseCase


def test_reply_parse_baseline_from_structured_payload():
    result = CoreLLMResult(
        status="ok",
        structured_data={"reply_text": "  Привет  ", "system_payload": {"lead_patch": {"first_name": "Ann"}}},
    )

    parsed = parse_provider_response(result)

    assert parsed == {
        "reply_text": "  Привет  ",
        "system_payload": {"lead_patch": {"first_name": "Ann"}},
    }


def test_reply_parse_rejects_non_structured_payload():
    result = CoreLLMResult(
        status="ok",
        text='```json\n{"reply_text":"ok","system_payload":{}}\n```',
        provider="vertex",
    )

    with pytest.raises(ValueError, match="structured payload is missing"):
        parse_provider_response(result)


def test_reply_parse_rejects_contract_regressions():
    result = CoreLLMResult(
        status="ok",
        structured_data={"reply_text": "ok", "system_payload": "not-object"},
    )

    with pytest.raises(ValueError, match="invalid_output"):
        parse_provider_response(result)


def test_generate_reply_use_case_keeps_runtime_reply_contract_shape():
    class _LLMServiceStub:
        async def run(self, task, payload, meta):
            assert task == "dialog_reply_task"
            assert "user_text" in payload
            assert "context" in payload
            assert "runtime_envelope" in payload
            assert "input" in payload
            assert payload["runtime_envelope"]["request_type"] == "primary_dialog_turn"
            assert payload["runtime_envelope"]["contract_version"] == "primary_runtime_envelope_v1"
            assert payload["runtime_envelope"]["backend_context"] == payload["context"]
            assert meta.channel == "telegram"
            return type("_R", (), {"data": {"reply_text": "hello", "system_payload": {"k": "v"}}})()

    use_case = GenerateReplyUseCase(llm_service=_LLMServiceStub())

    _, reply_text, system_payload, reply_meta = asyncio.run(use_case.execute(
        message={"message_id": "1"},
        channel="telegram",
        lead_id="lead-1",
        text="hi",
        llm_context={"foo": "bar"},
    ))

    assert reply_text == "hello"
    assert system_payload == {"k": "v"}
    assert reply_meta == {}


def test_vertex_reply_schema_keeps_only_first_name_in_lead_patch():
    schema = build_vertex_response_schema()
    lead_patch = schema["properties"]["system_payload"]["properties"]["lead_patch"]

    assert tuple(lead_patch["properties"].keys()) == ("first_name",)


def test_primary_agent_request_factory_embeds_backend_memory_contract_into_runtime_input():
    request = build_provider_request(
        {
            "model": "gemini-2.0-flash",
            "user_text": "hello again",
            "context": {"lead_snapshot": {"first_name": "Ann"}, "memory": {"rolling_summary": "Known client"}},
        }
    )

    assert "Treat backend context as authoritative runtime truth." in request.input
    assert "Do not greet the client as if this is the first conversation" in request.input
    assert "USER_MESSAGE:\nhello again" in request.input
    assert '"first_name": "Ann"' in request.input
    assert request.context == {
        "lead_snapshot": {"first_name": "Ann"},
        "memory": {"rolling_summary": "Known client"},
    }
