from __future__ import annotations

import asyncio
from dataclasses import dataclass

from src.use_cases.dialog.generate_reply_use_case import GenerateReplyUseCase


@dataclass
class _Result:
    ok: bool = True
    data: dict | None = None
    error: dict | None = None


class _LLMServiceStub:
    async def run(self, **_kwargs):
        return _Result(ok=True, data={"reply_text": "  hi  ", "system_payload": {"k": "v"}})


class _ProfileSpy:
    def __init__(self, *, validate_ok: bool = True, semantic_ok: bool = True) -> None:
        self.calls: list[str] = []
        self._validate_ok = validate_ok
        self._semantic_ok = semantic_ok

    def parse(self, raw_payload):
        self.calls.append("parse")
        return type("_T", (), {"reply_text": str(raw_payload.get("reply_text") or "").strip(), "system_payload": raw_payload.get("system_payload") or {}})()

    def validate(self, typed_output):
        _ = typed_output
        self.calls.append("validate")
        return type("_V", (), {"ok": self._validate_ok})()

    def semantic_validate(self, typed_output, context):
        _ = (typed_output, context)
        self.calls.append("semantic_validate")
        return type("_S", (), {"ok": self._semantic_ok})()


class _RegistryStub:
    def __init__(self, profile):
        self.profile = profile

    def get_profile(self, *, flow: str):
        assert flow == "primary_agent_reply_task"
        return self.profile


def test_reply_flow_runs_profile_pipeline_in_order():
    profile = _ProfileSpy()
    use_case = GenerateReplyUseCase(_LLMServiceStub(), profile_registry=_RegistryStub(profile))

    _, reply_text, system_payload, _ = asyncio.run(
        use_case.execute(message={}, channel="telegram", lead_id="lead-1", text="hello", llm_context={})
    )

    assert profile.calls == ["parse", "validate", "semantic_validate"]
    assert reply_text == "hi"
    assert system_payload == {"k": "v"}


def test_reply_flow_blocks_output_on_profile_contract_reject():
    profile = _ProfileSpy(validate_ok=False)
    use_case = GenerateReplyUseCase(_LLMServiceStub(), profile_registry=_RegistryStub(profile))

    result, reply_text, system_payload, _ = asyncio.run(
        use_case.execute(message={}, channel="telegram", lead_id="lead-1", text="hello", llm_context={})
    )

    assert result.ok is False
    assert result.error["kind"] == "contract_invalid"
    assert reply_text == ""
    assert system_payload is None
