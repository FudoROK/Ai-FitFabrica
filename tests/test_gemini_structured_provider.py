from __future__ import annotations

from dataclasses import dataclass

from src.domain.contracts import AgentOutput
from src.llm.core.request import LLMArtifact, LLMRequest
from src.llm.providers import gemini_structured_provider as module
from src.llm.providers.gemini_structured_provider import GeminiStructuredProvider


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


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text


class _VertexResponseEnvelope(_Response):
    def to_dict(self):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": self.text}],
                    }
                }
            ],
            "usage_metadata": {"total_token_count": 10},
        }


class _ModelsStub:
    def __init__(self, calls: dict[str, object], response: _Response) -> None:
        self._calls = calls
        self._response = response

    def generate_content(self, *, model, contents, config):
        self._calls["model_name"] = model
        self._calls["generate_content"] = {
            "content": contents,
            "generation_config": config,
        }
        return self._response


class _TypedConfigStub:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class _GenAiClientStub:
    def __init__(self, calls: dict[str, object], response: _Response) -> None:
        self.models = _ModelsStub(calls, response)


class _PartStub:
    @staticmethod
    def from_bytes(*, data: bytes, mime_type: str):
        return {"data": data, "mime_type": mime_type}


class _TypesStub:
    GenerateContentConfig = _TypedConfigStub
    HttpOptions = _TypedConfigStub
    Part = _PartStub


class _GenAiStub:
    def __init__(self, calls: dict[str, object], response: _Response) -> None:
        self._calls = calls
        self._response = response

    def Client(self, **kwargs):
        self._calls["client"] = kwargs
        return _GenAiClientStub(self._calls, self._response)


def _patch_genai(monkeypatch, calls: dict[str, object], response: _Response) -> None:
    monkeypatch.setattr(module, "genai", _GenAiStub(calls, response))
    monkeypatch.setattr(module, "types", _TypesStub)


def test_gemini_structured_provider_direct_call_with_transport_schema(monkeypatch):
    calls: dict[str, object] = {}
    response = _Response('{"reply_text":"ok","system_payload":{}}')
    _patch_genai(monkeypatch, calls, response)
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
    response = _Response('{"reply_text":"ok","system_payload":"not-object"}')
    _patch_genai(monkeypatch, calls, response)
    monkeypatch.setattr(module, "build_vertex_response_schema", lambda: {"type": "OBJECT"})

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(LLMRequest(task="dialog_reply_task", input="hello"))

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "invalid_output"


def test_gemini_structured_provider_supports_dialog_reply_task_alias(monkeypatch):
    calls: dict[str, object] = {}
    response = _Response('{"reply_text":"ok","system_payload":{}}')
    _patch_genai(monkeypatch, calls, response)
    monkeypatch.setattr(module, "build_vertex_response_schema", lambda: {"type": "OBJECT", "properties": {}})

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(LLMRequest(task="dialog_reply_task", input='{"user_text":"hello"}'))

    assert result.status == "ok"


def test_gemini_structured_provider_sends_resolved_image_with_text_prompt(monkeypatch):
    calls: dict[str, object] = {}
    response = _Response('{"confidence":0.94}')
    _patch_genai(monkeypatch, calls, response)

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(
        LLMRequest(
            task="human_identity_agent",
            input="Analyze the attached approved human photo.",
            artifacts=[
                LLMArtifact(
                    purpose="human_photo",
                    content_type="image/png",
                    payload=b"real-image-bytes",
                )
            ],
            structured_output={"schema": {"type": "object"}},
        )
    )

    assert result.status == "ok"
    assert calls["generate_content"]["content"] == [
        "Analyze the attached approved human photo.",
        {"data": b"real-image-bytes", "mime_type": "image/png"},
    ]


def test_gemini_structured_provider_honors_request_model_override(monkeypatch):
    calls: dict[str, object] = {}
    response = _Response('{"confidence":0.94}')
    _patch_genai(monkeypatch, calls, response)

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM(model="gemini-default")))
    result = provider.generate(
        LLMRequest(
            task="human_identity_agent",
            input="Analyze.",
            model="gemini-2.5-flash",
            structured_output={"schema": {"type": "object"}},
        )
    )

    assert result.status == "ok"
    assert calls["model_name"] == "gemini-2.5-flash"
    assert result.model == "gemini-2.5-flash"


def test_gemini_structured_provider_prefers_text_contract_over_vertex_response_envelope(monkeypatch):
    calls: dict[str, object] = {}
    response = _VertexResponseEnvelope('{"status":"ok"}')
    _patch_genai(monkeypatch, calls, response)

    provider = GeminiStructuredProvider(settings=_Settings(llm=_LLM()))
    result = provider.generate(
        LLMRequest(
            task="staging_provider_smoke",
            input="Return status.",
            structured_output={"schema": {"type": "object"}},
        )
    )

    assert result.status == "ok"
    assert result.structured_data == {"status": "ok"}
