from __future__ import annotations

from dataclasses import dataclass

from src.llm.contract_kinds import MEMORY_AGENT_OUTPUT_KIND, REPLY_AGENT_OUTPUT_KIND
from src.llm.core.request import LLMRequest
from src.llm.vertex import vertex_provider as vertex_provider_module
from src.llm.vertex.vertex_provider import VertexProvider
from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema


@dataclass
class _LLM:
    provider: str = "vertex"
    vertex_project: str = "proj"
    vertex_location: str = "us-central1"
    model: str = "gemini-2.0-flash"
    vertex_agent_resource: str | None = "projects/547855929194/locations/us-central1/reasoningEngines/123"


@dataclass
class _Settings:
    llm: _LLM


class _AgentEngineStub:
    def __init__(
        self,
        calls: dict[str, object],
        *,
        create_session_response: object = "session-1",
        stream_events: list[dict[str, object]] | None = None,
        get_session_response: object | None = None,
        stream_error: Exception | None = None,
    ):
        self._calls = calls
        self._create_session_response = create_session_response
        self._stream_events = stream_events or []
        self._get_session_response = get_session_response
        self._stream_error = stream_error

    def create_session(self, *, user_id: str):
        self._calls["create_session"] = {"user_id": user_id}
        return self._create_session_response

    def get_session(self, *, user_id: str, session_id: str):
        self._calls["get_session"] = {"user_id": user_id, "session_id": session_id}
        if self._get_session_response is None:
            raise RuntimeError("session not found")
        return self._get_session_response

    async def async_stream_query(self, *, user_id: str, session_id: str, message: str):
        self._calls["async_stream_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if self._stream_error is not None:
            raise self._stream_error
        for event in self._stream_events:
            yield event

    def stream_query(self, *, user_id: str, session_id: str, message: str):
        self._calls["stream_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if self._stream_error is not None:
            raise self._stream_error
        return self._stream_events

    def query(self, *, user_id: str, session_id: str, message: str):
        self._calls["query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if self._stream_error is not None:
            raise self._stream_error
        if self._stream_events:
            return self._stream_events[0]
        return {"output": {"reply_text": "", "system_payload": {}}}


class _AgentEngineContextAwareStub(_AgentEngineStub):
    async def async_stream_query(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str,
        context: dict[str, object] | None = None,
    ):
        self._calls["async_stream_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if context is not None:
            self._calls["async_stream_query"]["context"] = context
        if self._stream_error is not None:
            raise self._stream_error
        for event in self._stream_events:
            yield event


class _AgentEngineAsyncNoStructuredStreamStructuredStub(_AgentEngineStub):
    async def async_stream_query(self, *, user_id: str, session_id: str, message: str):
        self._calls["async_stream_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if self._stream_error is not None:
            raise self._stream_error
        for event in self._stream_events:
            yield event

    def stream_query(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str,
        response_mime_type: str | None = None,
        response_schema: dict[str, object] | None = None,
    ):
        self._calls["stream_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "response_mime_type": response_mime_type,
            "response_schema": response_schema,
        }
        if self._stream_error is not None:
            raise self._stream_error
        return self._stream_events


class _AgentEnginesModuleStub:
    def __init__(
        self,
        *,
        create_session_response: object = "session-1",
        stream_events: list[dict[str, object]] | None = None,
        get_session_response: object | None = None,
        stream_error: Exception | None = None,
    ):
        self.calls: dict[str, object] = {}
        self._create_session_response = create_session_response
        self._stream_events = stream_events
        self._get_session_response = get_session_response
        self._stream_error = stream_error

    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _AgentEngineNoAsyncStub(_AgentEngineStub):
    async_stream_query = None


class _AgentEngineQueryOnlyStub(_AgentEngineStub):
    async_stream_query = None
    stream_query = None


class _AgentEngineAsyncOnlyNoStructuredStub(_AgentEngineStub):
    stream_query = None
    query = None

    async def async_stream_query(self, *, user_id: str, session_id: str, message: str):
        self._calls["async_stream_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if self._stream_error is not None:
            raise self._stream_error
        for event in self._stream_events:
            yield event


class _AgentEngineAsyncQueryOnlyStub(_AgentEngineStub):
    async_stream_query = None
    stream_query = None
    query = None

    async def async_query(self, *, user_id: str, session_id: str, message: str):
        self._calls["async_query"] = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        if self._stream_error is not None:
            raise self._stream_error
        if self._stream_events:
            return self._stream_events[0]
        return {"output": {"reply_text": "", "system_payload": {}}}


class _AgentEnginesModuleNoAsyncStub(_AgentEnginesModuleStub):
    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineNoAsyncStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _AgentEnginesModuleQueryOnlyStub(_AgentEnginesModuleStub):
    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineQueryOnlyStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _AgentEnginesModuleAsyncOnlyNoStructuredStub(_AgentEnginesModuleStub):
    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineAsyncOnlyNoStructuredStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _AgentEnginesModuleAsyncQueryOnlyStub(_AgentEnginesModuleStub):
    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineAsyncQueryOnlyStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _AgentEnginesModuleContextAwareStub(_AgentEnginesModuleStub):
    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineContextAwareStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _AgentEnginesModuleAsyncNoStructuredStreamStructuredStub(_AgentEnginesModuleStub):
    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _AgentEngineAsyncNoStructuredStreamStructuredStub(
            self.calls,
            create_session_response=self._create_session_response,
            stream_events=self._stream_events,
            get_session_response=self._get_session_response,
            stream_error=self._stream_error,
        )


class _RetryingAgentEngineStub(_AgentEngineStub):
    def __init__(self, calls: dict[str, object], *, successful_payload: dict[str, object]):
        super().__init__(calls, stream_events=[{"output": successful_payload}])
        self._attempt = 0

    async def async_stream_query(self, *, user_id: str, session_id: str, message: str):
        self._attempt += 1
        self._calls.setdefault("attempts", []).append(self._attempt)
        if self._attempt == 1:
            class _RateLimitError(Exception):
                status_code = 429

            raise _RateLimitError("retry please")
        async for event in super().async_stream_query(user_id=user_id, session_id=session_id, message=message):
            yield event


class _RetryingAgentEnginesModuleStub(_AgentEnginesModuleStub):
    def __init__(self, *, successful_payload: dict[str, object]):
        super().__init__(stream_events=[])
        self._successful_payload = successful_payload

    def get(self, agent_resource: str):
        self.calls["agent_engines_get"] = {"agent_resource": agent_resource}
        return _RetryingAgentEngineStub(self.calls, successful_payload=self._successful_payload)


def _request(payload: str = '{"user_text":"hello","context":{"source":"telegram"}}') -> LLMRequest:
    return LLMRequest(
        task="primary_agent_reply_task",
        input=payload,
        structured_output={"kind": REPLY_AGENT_OUTPUT_KIND, "schema": build_vertex_response_schema()},
    )


def _patch_reasoning_engines(monkeypatch, engine_stub):
    monkeypatch.setattr(vertex_provider_module, "agent_engines", engine_stub)
    monkeypatch.setattr(vertex_provider_module, "reasoning_engines", engine_stub)


def test_vertex_provider_queries_reasoning_engine_success_path(monkeypatch):
    payload = {
        "reply_text": "Здравствуйте",
        "system_payload": {
            "lead_patch": {
                "first_name": "Анна",
                "full_name": "Анна Каренина",
                "pain_points": ["slow response"],
                "needs": ["crm"],
            }
        },
    }
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)

    provider = VertexProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(_request())

    assert result.status == "ok"
    assert result.structured_data == payload
    assert result.provider == "vertex"
    assert result.model == "projects/547855929194/locations/us-central1/reasoningEngines/123"
    assert result.provider_metadata["execution_path"] == "reasoning_engine_session_stream"
    assert result.provider_metadata["vertex_session_id"] == "session-1"
    assert result.provider_metadata["vertex_session_created"] is True

    init_call = engine_stub.calls["agent_engines_get"]
    assert init_call == {"agent_resource": "projects/547855929194/locations/us-central1/reasoningEngines/123"}
    assert engine_stub.calls["create_session"] == {"user_id": "telegram:unknown"}
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_does_not_forward_structured_kwargs_to_reasoning_engine(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    schema = {
        "type": "OBJECT",
        "required": ["reply_text", "system_payload"],
        "properties": {
            "reply_text": {"type": "STRING"},
            "system_payload": {"type": "OBJECT"},
        },
    }
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(
        LLMRequest(
            task="primary_agent_reply_task",
            input='{"user_text":"hello"}',
            structured_output={"schema": schema, "kind": REPLY_AGENT_OUTPUT_KIND, "required": True},
        )
    )

    assert result.status == "ok"
    assert result.structured_data == payload
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }
    assert "query" not in engine_stub.calls
    assert "stream_query" not in engine_stub.calls
    assert result.provider_metadata["vertex_structured_requested"] is True
    assert result.provider_metadata["vertex_structured_enforced"] is False
    assert result.provider_metadata["vertex_structured_mode"] == "disabled"
    assert result.provider_metadata["contract_kind"] == REPLY_AGENT_OUTPUT_KIND
    assert result.provider_metadata["contract_required"] is True
    assert result.provider_metadata["contract_enforced"] is False
    assert result.provider_metadata["runtime_contract_version"] == "vertex_transport_blackbox_v1"
def test_vertex_provider_uses_minimal_invocation_contract_even_when_structured_requested(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(
        LLMRequest(
            task="primary_agent_reply_task",
            input='{"user_text":"hello"}',
            structured_output={"schema": {"type": "OBJECT"}, "kind": REPLY_AGENT_OUTPUT_KIND},
        )
    )

    assert result.status == "ok"
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }
    assert result.provider_metadata["vertex_structured_requested"] is True
    assert result.provider_metadata["vertex_structured_mode"] == "disabled"
    assert result.provider_metadata["vertex_structured_enforced"] is False

def test_vertex_provider_uses_streaming_when_required_structured_contract_has_only_streaming_transport(monkeypatch):
    engine_stub = _AgentEnginesModuleAsyncOnlyNoStructuredStub(
        stream_events=[{"output": {"reply_text": "ok", "system_payload": {}}}]
    )
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(
        LLMRequest(
            task="primary_agent_reply_task",
            input='{"user_text":"hello"}',
            structured_output={"schema": {"type": "OBJECT"}, "kind": REPLY_AGENT_OUTPUT_KIND, "required": True},
        )
    )

    assert result.status == "ok"
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_uses_streaming_when_structured_contract_required(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    schema = {"type": "OBJECT", "required": ["reply_text", "system_payload"]}
    engine_stub = _AgentEnginesModuleAsyncNoStructuredStreamStructuredStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(
        LLMRequest(
            task="primary_agent_reply_task",
            input='{"user_text":"hello"}',
            structured_output={"schema": schema, "kind": REPLY_AGENT_OUTPUT_KIND, "required": True},
        )
    )

    assert result.status == "ok"
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_uses_raw_input_as_user_text_when_payload_not_json(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request(payload="plain user message"))

    assert result.status == "ok"
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "plain user message",
    }


def test_vertex_provider_accepts_content_dict_structured_payload(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"content": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request())

    assert result.status == "ok"
    assert result.structured_data == payload


def test_vertex_provider_returns_invalid_output_when_stream_is_empty(monkeypatch):
    engine_stub = _AgentEnginesModuleStub(stream_events=[])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request())

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "invalid_output"


def test_vertex_provider_returns_invalid_output_when_structured_payload_missing(monkeypatch):
    engine_stub = _AgentEnginesModuleStub(create_session_response={"unexpected": "shape"})
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request())

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "invalid_output"


def test_vertex_provider_classifies_http_errors(monkeypatch):
    class _RateLimitError(Exception):
        status_code = 429

    engine_stub = _AgentEnginesModuleStub(
        stream_events=[],
        stream_error=_RateLimitError("too many requests"),
    )
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request())

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "rate_limited"
    assert result.error.retriable is True


def test_vertex_provider_compatibility_with_llm_result_contract(monkeypatch):
    payload = {
        "reply_text": "ok",
        "system_payload": {"lead_patch": {"first_name": "A", "full_name": "A B", "pain_points": [], "needs": []}},
    }
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    req = LLMRequest(task="primary_agent_reply_task", input="hello", max_retries=1)
    result = provider.generate(req)

    assert result.status == "ok"
    assert isinstance(result.text, str)
    assert result.text == '{"reply_text": "ok", "system_payload": {"lead_patch": {"first_name": "A", "full_name": "A B", "pain_points": [], "needs": []}}}'
    assert result.structured_data == payload
    assert result.retry_count == 0


def test_vertex_provider_falls_back_to_stream_query_when_async_is_missing(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleNoAsyncStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request())

    assert result.status == "ok"
    assert engine_stub.calls["stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_falls_back_to_query_when_stream_is_missing(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleQueryOnlyStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(_request())

    assert result.status == "ok"
    assert engine_stub.calls["query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_falls_back_to_async_query_when_stream_methods_are_missing(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleAsyncQueryOnlyStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(
        LLMRequest(
            task="primary_agent_reply_task",
            input='{"user_text":"hello"}',
            structured_output={"schema": {"type": "OBJECT"}, "kind": REPLY_AGENT_OUTPUT_KIND, "required": True},
        )
    )

    assert result.status == "ok"
    assert engine_stub.calls["async_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_reuses_existing_session_from_context(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleStub(
        stream_events=[{"output": payload}],
        get_session_response={"id": "existing-session"},
    )
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    request = _request(payload='{"user_text":"hello","context":{"session":{"vertex_session_id":"existing-session"}}}')
    result = provider.generate(request)

    assert result.status == "ok"
    assert engine_stub.calls["get_session"] == {
        "user_id": "telegram:unknown",
        "session_id": "existing-session",
    }
    assert "create_session" not in engine_stub.calls
    assert result.provider_metadata["vertex_session_created"] is False


def test_vertex_provider_keeps_context_out_of_transport_call(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleContextAwareStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    request = _request(payload='{"user_text":"hello","context":{"source":"telegram","trace_id":"abc"}}')
    result = provider.generate(request)

    assert result.status == "ok"
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:unknown",
        "session_id": "session-1",
        "message": "hello",
    }


def test_vertex_provider_uses_sales_runtime_envelope_as_message_and_identity_source(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleStub(
        stream_events=[{"output": payload}],
        get_session_response={"id": "existing-session"},
    )
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    envelope = (
        '{"request_type":"sales_dialog_turn","contract_version":"primary_runtime_envelope_v1",'
        '"user_text":"hello","backend_context":{"identity":{"channel":"telegram","external_user_id":"42"},'
        '"session":{"vertex_session_id":"existing-session"}}}'
    )
    result = provider.generate(LLMRequest(task="primary_reply_task", input=envelope, structured_output={"kind": REPLY_AGENT_OUTPUT_KIND, "schema": build_vertex_response_schema()}))

    assert result.status == "ok"
    assert engine_stub.calls["get_session"] == {
        "user_id": "telegram:42",
        "session_id": "existing-session",
    }
    assert engine_stub.calls["async_stream_query"] == {
        "user_id": "telegram:42",
        "session_id": "existing-session",
        "message": envelope,
    }


def test_vertex_provider_enforces_timeout_path(monkeypatch):
    payload = {"reply_text": "ok", "system_payload": {}}
    engine_stub = _AgentEnginesModuleStub(stream_events=[{"output": payload}])
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()), timeout_s=0.001)

    ticks = iter([0.0, 0.0, 1.0, 1.0])
    monkeypatch.setattr(vertex_provider_module.time, "perf_counter", lambda: next(ticks))
    import src.llm.vertex.vertex_invocation as vertex_invocation_module

    monkeypatch.setattr(vertex_invocation_module.time, "perf_counter", lambda: next(ticks))

    result = provider.generate(_request())

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "timeout"


def test_vertex_provider_retries_retriable_errors_and_keeps_contract(monkeypatch):
    payload = {"reply_text": "ok after retry", "system_payload": {}}
    engine_stub = _RetryingAgentEnginesModuleStub(successful_payload=payload)
    _patch_reasoning_engines(monkeypatch, engine_stub)
    provider = VertexProvider(settings=_Settings(llm=_LLM()))

    result = provider.generate(LLMRequest(task="primary_agent_reply_task", input='{"user_text":"hello"}', max_retries=1))

    assert result.status == "ok"
    assert result.structured_data == payload
    assert result.retry_count == 1
    assert engine_stub.calls["attempts"] == [1, 2]
