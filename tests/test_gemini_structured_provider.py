from __future__ import annotations

from dataclasses import dataclass

from src.domain.contracts import AgentOutput
from src.llm.core.request import LLMRequest
from src.llm.providers import gemini_structured_provider as module
from src.llm.providers.gemini_structured_provider import GeminiStructuredProvider
from src.runtime_agents.memory_agent.memory_response_parser import parse_provider_response as parse_memory_provider_response
from src.runtime_agents.memory_agent.contracts import DailyMemoryContract, RollingMemoryContract


@dataclass
class _LLM:
    provider: str = "gemini_structured"
    vertex_project: str = "proj"
    vertex_location: str = "us-central1"
    model: str = "gemini-2.0-flash"
    vertex_agent_resource: str | None = None


@dataclass
class _Settings:
    llm: _LLM


class _VertexAiStub:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def init(self, *, project: str, location: str) -> None:
        self.calls.append({"project": project, "location": location})


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text


class _RichResponse:
    def __init__(self, payload: dict[str, object], text: str = "") -> None:
        self._payload = payload
        self.text = text

    def to_dict(self) -> dict[str, object]:
        return self._payload


class _ModelStub:
    def __init__(self, model_name: str, calls: dict[str, object], response: _Response) -> None:
        calls["model_name"] = model_name
        self._calls = calls
        self._response = response

    def generate_content(self, content, generation_config=None, stream=False, request_options=None):
        self._calls["generate_content"] = {
            "content": content,
            "generation_config": generation_config,
            "stream": stream,
            "request_options": request_options,
        }
        return self._response


class _GenerationConfigStub:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _GenerativeModelsStub:
    def __init__(self, calls: dict[str, object], response: _Response) -> None:
        self._calls = calls
        self._response = response
        self.GenerationConfig = _GenerationConfigStub

    def GenerativeModel(self, model_name: str):
        return _ModelStub(model_name, self._calls, self._response)


def _canonical_rolling_update_json() -> str:
    return (
        '{"rolling_summary_text":"rolling","open_questions":[],"carry_forward_notes":[],'
        '"days_count":1,"last_daily_summary_date":"2025-01-01","version":1}'
    )


def _canonical_rolling_update_dict() -> dict[str, object]:
    return {
        "rolling_summary_text": "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.",
        "open_questions": [],
        "carry_forward_notes": [],
        "days_count": 1,
        "last_daily_summary_date": "2025-01-01",
        "version": 1,
    }


def test_gemini_structured_provider_direct_call_with_transport_schema(monkeypatch):
    calls: dict[str, object] = {}
    vertexai_stub = _VertexAiStub()
    response = _Response('{"reply_text":"ok","system_payload":{}}')
    generative_stub = _GenerativeModelsStub(calls, response)

    monkeypatch.setattr(module, "vertexai", vertexai_stub)
    monkeypatch.setattr(module, "generative_models", generative_stub)
    monkeypatch.setattr(module, "build_vertex_response_schema", lambda: {"type": "OBJECT", "properties": {}})

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(LLMRequest(task="dialog_reply_task", input='{"user_text":"hello"}'))

    assert result.status == "ok"
    expected = AgentOutput.model_validate({"reply_text": "ok", "system_payload": {}}).model_dump(mode="python")
    validated = AgentOutput.model_validate(result.structured_data).model_dump(mode="python")
    assert validated == expected
    assert result.provider_metadata["response_mime_type"] == "application/json"


def test_gemini_structured_provider_rejects_semantically_invalid_payload(monkeypatch):
    calls: dict[str, object] = {}
    vertexai_stub = _VertexAiStub()
    response = _Response('{"reply_text":"ok","system_payload":"not-object"}')
    generative_stub = _GenerativeModelsStub(calls, response)

    monkeypatch.setattr(module, "vertexai", vertexai_stub)
    monkeypatch.setattr(module, "generative_models", generative_stub)
    monkeypatch.setattr(module, "build_vertex_response_schema", lambda: {"type": "OBJECT"})

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(LLMRequest(task="dialog_reply_task", input="hello"))

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "invalid_output"


def test_gemini_structured_provider_daily_memory_sync_uses_request_schema(monkeypatch):
    calls: dict[str, object] = {}
    vertexai_stub = _VertexAiStub()
    response = _Response(
        '{"daily_summary":{"summary_text":"daily from memory task"},"active_window_update":null,"conversation_state_update":null}'
    )
    generative_stub = _GenerativeModelsStub(calls, response)

    monkeypatch.setattr(module, "vertexai", vertexai_stub)
    monkeypatch.setattr(module, "generative_models", generative_stub)

    memory_schema = DailyMemoryContract.model_json_schema()
    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(
        LLMRequest(
            task="memory_daily_sync_task",
            input='{"messages":[]}',
            structured_output={"name": "memory_agent_output", "schema": memory_schema},
        )
    )

    assert result.status == "ok"
    assert result.structured_data["daily_summary"]["summary_text"] == "daily from memory task"
    cfg = calls["generate_content"]["generation_config"]
    assert isinstance(cfg, _GenerationConfigStub)
    assert cfg.kwargs["response_schema"] == memory_schema


def test_gemini_structured_provider_rolling_memory_sync_uses_request_schema(monkeypatch):
    calls: dict[str, object] = {}
    vertexai_stub = _VertexAiStub()
    response = _Response('{"rolling_update":' + _canonical_rolling_update_json() + '}')
    generative_stub = _GenerativeModelsStub(calls, response)

    monkeypatch.setattr(module, "vertexai", vertexai_stub)
    monkeypatch.setattr(module, "generative_models", generative_stub)

    memory_schema = RollingMemoryContract.model_json_schema()
    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(
        LLMRequest(
            task="memory_rolling_sync_task",
            input='{"messages":[]}',
            structured_output={"name": "memory_agent_output", "schema": memory_schema},
        )
    )

    assert result.status == "ok"
    assert result.structured_data["rolling_update"]["rolling_summary_text"] == "rolling"
    cfg = calls["generate_content"]["generation_config"]
    assert isinstance(cfg, _GenerationConfigStub)
    assert cfg.kwargs["response_schema"] == memory_schema


def test_gemini_structured_provider_requires_schema_for_non_reply_tasks(monkeypatch):
    calls: dict[str, object] = {}
    vertexai_stub = _VertexAiStub()
    response = _Response('{"daily_summary":{"summary_text":"daily"}}')
    generative_stub = _GenerativeModelsStub(calls, response)

    monkeypatch.setattr(module, "vertexai", vertexai_stub)
    monkeypatch.setattr(module, "generative_models", generative_stub)

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(
        LLMRequest(
            task="memory_daily_sync_task",
            input='{"messages":[]}',
            structured_output=None,
        )
    )

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "bad_request"


def test_gemini_structured_provider_keeps_legacy_reply_task_alias(monkeypatch):
    calls: dict[str, object] = {}
    vertexai_stub = _VertexAiStub()
    response = _Response('{"reply_text":"ok","system_payload":{}}')
    generative_stub = _GenerativeModelsStub(calls, response)

    monkeypatch.setattr(module, "vertexai", vertexai_stub)
    monkeypatch.setattr(module, "generative_models", generative_stub)
    monkeypatch.setattr(module, "build_vertex_response_schema", lambda: {"type": "OBJECT", "properties": {}})

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(LLMRequest(task="dialog_reply_task", input='{"user_text":"hello"}'))

    assert result.status == "ok"
