from __future__ import annotations

from dataclasses import dataclass

from src.llm.core.request import LLMArtifact, LLMRequest
from src.llm.providers import gemini_structured_client


class _GenerateContentConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


@dataclass
class _HttpOptions:
    timeout: int


class _Part:
    @staticmethod
    def from_bytes(*, data: bytes, mime_type: str):
        return {"data": data, "mime_type": mime_type}


class _TypesStub:
    GenerateContentConfig = _GenerateContentConfig
    HttpOptions = _HttpOptions
    Part = _Part


class _ModelsStub:
    def __init__(self, calls: dict[str, object]) -> None:
        self._calls = calls

    def generate_content(self, **kwargs):
        self._calls["generate_content"] = kwargs
        return {"text": '{"status":"ok"}'}


@dataclass
class _ClientStub:
    models: _ModelsStub


class _GenAiStub:
    def __init__(self, calls: dict[str, object]) -> None:
        self._calls = calls

    def Client(self, **kwargs):
        self._calls["client"] = kwargs
        return _ClientStub(models=_ModelsStub(self._calls))


def test_get_client_builds_google_genai_vertex_client() -> None:
    calls: dict[str, object] = {}

    client = gemini_structured_client.get_client(
        current_client=None,
        project="project-1",
        location="europe-west1",
        genai_module=_GenAiStub(calls),
    )

    assert isinstance(client, _ClientStub)
    assert calls["client"] == {
        "vertexai": True,
        "project": "project-1",
        "location": "europe-west1",
    }


def test_invoke_model_uses_typed_google_genai_config_and_multimodal_parts() -> None:
    calls: dict[str, object] = {}
    client = _ClientStub(models=_ModelsStub(calls))
    request = LLMRequest(
        task="garment_identity_agent",
        input="Analyze the approved garment.",
        temperature=0.2,
        artifacts=[
            LLMArtifact(
                purpose="garment_photo",
                content_type="image/webp",
                payload=b"garment-image",
            )
        ],
        structured_output={"schema": {"type": "object"}},
    )

    gemini_structured_client.invoke_model(
        client=client,
        model="gemini-2.5-flash",
        request=request,
        response_schema={"type": "object"},
        response_mime_type="application/json",
        timeout_s=90.0,
        types_module=_TypesStub,
    )

    call = calls["generate_content"]
    assert call["model"] == "gemini-2.5-flash"
    assert call["contents"] == [
        "Analyze the approved garment.",
        {"data": b"garment-image", "mime_type": "image/webp"},
    ]
    assert call["config"].kwargs == {
        "response_mime_type": "application/json",
        "response_json_schema": {"type": "object"},
        "temperature": 0.2,
        "http_options": _HttpOptions(timeout=90_000),
    }
