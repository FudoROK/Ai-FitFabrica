import asyncio
from types import SimpleNamespace

from src.llm import LLMMeta, LLMService
from src.llm.contract_kinds import REPLY_AGENT_OUTPUT_KIND
from src.llm.core.request import LLMRequest
from src.llm.core.result import LLMResult as CoreLLMResult
from src.llm.core.types import LLMError
from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema


class FakeProvider:
    provider_name = "fake"

    def __init__(self, result: CoreLLMResult | list[CoreLLMResult]):
        self.results = result if isinstance(result, list) else [result]
        self.calls = 0
        self.last_request: LLMRequest | None = None

    def generate(self, request: LLMRequest) -> CoreLLMResult:
        self.calls += 1
        self.last_request = request
        idx = min(self.calls - 1, len(self.results) - 1)
        return self.results[idx]


def _build_settings(*, provider: str = "vertex", mode: str = "live"):
    return SimpleNamespace(
        llm=SimpleNamespace(
            provider=provider,
            mode=mode,
            model="gemini-2.0-flash",
            vertex_project="vertex-proj",
            vertex_location="us-central1",
            vertex_agent_resource="projects/p/locations/us-central1/reasoningEngines/1",
        )
    )


def test_llm_service_reply_uses_injected_runtime_provider():
    primary_provider = FakeProvider(CoreLLMResult(status="ok", text="unused", provider="fake", model="fake-model"))
    structured_provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={"reply_text": "structured-reply", "system_payload": {"lead_patch": {"first_name": "Ann"}}},
            provider="gemini_structured",
            model="fake-model",
            retry_count=0,
        )
    )
    service = LLMService(provider=primary_provider, mode="live")
    service._reply_structured_provider = structured_provider

    result = asyncio.run(service.run(task="dialog_reply_task", payload={"user_text": "hi", "context": None}, meta=LLMMeta(trace_id="t-1")))

    assert result.ok is True
    assert result.data["reply_text"] == "structured-reply"
    assert structured_provider.calls == 1
    assert primary_provider.calls == 0


def test_llm_service_reply_builds_provider_neutral_request():
    structured_provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={"reply_text": "hello", "system_payload": {}},
            provider="gemini_structured",
            model="fake-model",
        )
    )
    service = LLMService(provider=FakeProvider(CoreLLMResult(status="ok", text="unused", provider="fake", model="fake-model")), mode="live")
    service._reply_structured_provider = structured_provider

    result = asyncio.run(service.run(task="dialog_reply_task", payload={"user_text": "hi"}, meta=LLMMeta(trace_id="t-1")))

    assert result.ok is True
    assert structured_provider.last_request is not None
    assert "USER_MESSAGE:\nhi" in structured_provider.last_request.input
    assert "BACKEND_CONTEXT_JSON:\n{}" in structured_provider.last_request.input
    assert "Treat backend context as authoritative runtime truth." in structured_provider.last_request.input
    assert structured_provider.last_request.context == {}
    assert structured_provider.last_request.structured_output == {
        "kind": REPLY_AGENT_OUTPUT_KIND,
        "schema": build_vertex_response_schema(),
    }


def test_llm_service_profile_extract_uses_provider_json():
    provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={
                "lead_patch": {
                    "first_name": "A",
                    "business_type": "x",
                    "business_description": "",
                    "pain_points": "y",
                    "needs": "z",
                    "recommended_package": "",
                },
                "missing": [],
                "confidence": 0.8,
            },
            provider="fake",
            model="fake-model",
            retry_count=0,
        )
    )
    service = LLMService(provider=provider, mode="live")

    result = asyncio.run(
        service.run(
            task="profile_extract_task",
            payload={"user_message": "u", "assistant_message": "a", "history": []},
            meta=LLMMeta(),
        )
    )

    assert result.ok is True
    assert "lead_patch" in result.data["profile"]


def test_llm_service_invalid_output_is_handled_without_fallback_retry():
    provider = FakeProvider([
        CoreLLMResult(
            status="error",
            provider="fake",
            model="fake-model",
            retry_count=0,
            error=LLMError(type="invalid_output", message_redacted="schema mismatch", retriable=False),
        ),
        CoreLLMResult(
            status="ok",
            text="{}",
            provider="fake",
            model="fake-model",
            retry_count=0,
        ),
    ])
    service = LLMService(provider=provider, mode="live")

    result = asyncio.run(
        service.run(
            task="profile_extract_task",
            payload={"user_message": "u", "assistant_message": "a", "history": []},
            meta=LLMMeta(),
        )
    )

    assert result.ok is False
    assert result.error["kind"] == "invalid_output"
    assert provider.calls == 1


def test_llm_service_non_live_returns_stub_for_reply():
    provider = FakeProvider(CoreLLMResult(status="ok", text="unused", provider="fake", model="fake-model"))
    service = LLMService(provider=provider, mode="stub")

    result = asyncio.run(service.run(task="dialog_reply_task", payload={"user_text": "hi"}, meta=LLMMeta()))

    assert result.ok is False
    assert result.data["reply_text"] == ""
    assert result.error["message"] == "reply_unavailable"
    assert provider.calls == 0
