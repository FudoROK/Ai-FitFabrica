import asyncio
from types import SimpleNamespace

from src.llm import LLMMeta, LLMService
from src.llm.contract_kinds import MEMORY_DAILY_OUTPUT_KIND, REPLY_AGENT_OUTPUT_KIND
from src.llm.core.request import LLMRequest
from src.llm.core.result import LLMResult as CoreLLMResult
from src.llm.core.types import LLMError
from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema
from src.runtime_agents.memory_agent.contracts import DailyMemoryContract


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


def _build_settings(
    *,
    provider: str = "vertex",
    mode: str = "live",
    memory_daily_resource: str | None = None,
    memory_rolling_resource: str | None = None,
):
    return SimpleNamespace(
        llm=SimpleNamespace(
            provider=provider,
            mode=mode,
            model="gemini-2.0-flash",
            vertex_project="vertex-proj",
            vertex_location="us-central1",
            vertex_agent_resource="projects/p/locations/us-central1/reasoningEngines/1",
            vertex_memory_daily_agent_resource=memory_daily_resource,
            vertex_memory_rolling_agent_resource=memory_rolling_resource,
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

    result = asyncio.run(service.run(task="primary_agent_reply_task", payload={"user_text": "hi", "context": None}, meta=LLMMeta(trace_id="t-1")))

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

    result = asyncio.run(service.run(task="primary_agent_reply_task", payload={"user_text": "hi"}, meta=LLMMeta(trace_id="t-1")))

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

    result = asyncio.run(service.run(task="primary_agent_reply_task", payload={"user_text": "hi"}, meta=LLMMeta()))

    assert result.ok is False
    assert result.data["reply_text"] == ""
    assert result.error["message"] == "reply_unavailable"
    assert provider.calls == 0


def test_llm_service_memory_sync_uses_dedicated_memory_vertex_resource_when_configured(monkeypatch):
    primary_provider = FakeProvider(CoreLLMResult(status="ok", text="legacy", provider="fake", model="legacy-model"))
    memory_provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={
                "active_window_update": None,
                "daily_summary": {"summary_text": "from-memory-runtime"},
                "conversation_state_update": None,
            },
            provider="vertex",
            model="memory-model",
        )
    )

    monkeypatch.setattr(
        "src.llm.llm_service.VertexProvider",
        lambda settings, agent_resource_override=None: memory_provider,
    )
    service = LLMService(
        provider=primary_provider,
        mode="live",
        settings=_build_settings(
            provider="vertex",
            memory_daily_resource="projects/p/locations/us-central1/reasoningEngines/99",
        ),
    )

    result = asyncio.run(
        service.run(
            task="memory_daily_sync_task",
            payload={
                "lead_snapshot": {"first_name": "Ann"},
                "closed_active_window": {"messages": [{"role": "user", "text": "x"}]},
                "rolling_summary": "",
                "conversation_state": {},
                "timezone": "UTC",
            },
            meta=LLMMeta(trace_id="trace-memory-sync-resource"),
        )
    )

    assert result.ok is True
    assert result.data["daily_summary"]["summary_text"] == "from-memory-runtime"
    assert memory_provider.calls == 1
    assert primary_provider.calls == 0


def test_llm_service_memory_tasks_fail_fast_when_daily_memory_resource_is_missing():
    primary_provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={
                "active_window_update": None,
                "daily_summary": {"summary_text": "from-primary-runtime"},
                "conversation_state_update": None,
            },
            provider="vertex",
            model="primary-model",
        )
    )
    service = LLMService(
        provider=primary_provider,
        mode="live",
        settings=_build_settings(provider="vertex", memory_daily_resource=None),
    )

    result = asyncio.run(
        service.run(
            task="memory_daily_sync_task",
            payload={
                "lead_snapshot": {"first_name": "Ann"},
                "closed_active_window": {"messages": [{"role": "user", "text": "x"}]},
                "rolling_summary": "",
                "conversation_state": {},
                "timezone": "UTC",
            },
            meta=LLMMeta(trace_id="trace-memory-resource-missing"),
        )
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error["kind"] == "ROUTING_ERROR"
    assert "VERTEX_MEMORY_DAILY_AGENT_RESOURCE" in result.error["message"]
    assert primary_provider.calls == 0


def test_llm_service_memory_tasks_fail_fast_when_rolling_memory_resource_is_missing():
    primary_provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={"rolling_update": _canonical_rolling_update("from-primary-runtime")},
            provider="vertex",
            model="primary-model",
        )
    )
    service = LLMService(
        provider=primary_provider,
        mode="live",
        settings=_build_settings(provider="vertex", memory_daily_resource="projects/p/locations/us-central1/reasoningEngines/99"),
    )

    result = asyncio.run(
        service.run(
            task="memory_rolling_sync_task",
            payload={
                "prior_rolling_memory": {"rolling_summary_text": "previous"},
                "new_daily_summary": {"summary_text": "daily", "memory_day_key": "2026-01-01"},
            },
            meta=LLMMeta(trace_id="trace-memory-rolling-resource-missing"),
        )
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error["kind"] == "ROUTING_ERROR"
    assert "VERTEX_MEMORY_ROLLING_AGENT_RESOURCE" in result.error["message"]
    assert primary_provider.calls == 0


def test_llm_service_rolling_sync_uses_dedicated_rolling_vertex_resource_when_configured(monkeypatch):
    primary_provider = FakeProvider(CoreLLMResult(status="ok", text="legacy", provider="fake", model="legacy-model"))
    rolling_provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={"rolling_update": _canonical_rolling_update("from-rolling-runtime")},
            provider="vertex",
            model="rolling-model",
        )
    )

    monkeypatch.setattr(
        "src.llm.llm_service.VertexProvider",
        lambda settings, agent_resource_override=None: rolling_provider,
    )
    service = LLMService(
        provider=primary_provider,
        mode="live",
        settings=_build_settings(
            provider="vertex",
            memory_daily_resource="projects/p/locations/us-central1/reasoningEngines/99",
            memory_rolling_resource="projects/p/locations/us-central1/reasoningEngines/199",
        ),
    )

    result = asyncio.run(
        service.run(
            task="memory_rolling_sync_task",
            payload={
                "prior_rolling_memory": {"rolling_summary_text": "prev"},
                "new_daily_summary": {"summary_text": "daily", "memory_day_key": "2026-01-01"},
            },
            meta=LLMMeta(trace_id="trace-memory-rolling-sync-resource"),
        )
    )

    assert result.ok is True
    assert result.data["rolling_update"]["rolling_summary_text"] == "from-rolling-runtime"
    assert rolling_provider.calls == 1
    assert primary_provider.calls == 0


def test_llm_service_daily_memory_sync_builds_structured_contract_request():
    provider = FakeProvider(
        CoreLLMResult(
            status="ok",
            structured_data={
                "active_window_update": None,
                "daily_summary": {"summary_text": "ok"},
                "conversation_state_update": None,
            },
            provider="vertex",
            model="memory-model",
        )
    )
    service = LLMService(
        provider=FakeProvider(CoreLLMResult(status="ok", text="unused", provider="fake", model="fake-model")),
        mode="live",
        settings=_build_settings(
            provider="vertex",
            memory_daily_resource="projects/p/locations/us-central1/reasoningEngines/99",
        ),
    )
    service._memory_daily_runtime_provider = provider

    result = asyncio.run(
        service.run(
            task="memory_daily_sync_task",
            payload={
                "lead_snapshot": {"first_name": "Ann"},
                "closed_active_window": {"messages": []},
                "rolling_summary": "",
                "conversation_state": {},
                "timezone": "UTC",
            },
            meta=LLMMeta(),
        )
    )

    assert result.ok is True
    assert provider.last_request is not None
    assert provider.last_request.structured_output == {
        "kind": MEMORY_DAILY_OUTPUT_KIND,
        "strict": True,
        "schema": DailyMemoryContract.model_json_schema(),
    }
