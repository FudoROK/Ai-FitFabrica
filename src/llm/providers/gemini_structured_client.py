"""Google Gen AI SDK client helpers for structured Gemini generation."""

from __future__ import annotations

import importlib
import importlib.util

_GENAI_SPEC = importlib.util.find_spec("google.genai")
genai = importlib.import_module("google.genai") if _GENAI_SPEC is not None else None
types = importlib.import_module("google.genai.types") if _GENAI_SPEC is not None else None


def get_client(
    *,
    current_client: object | None,
    project: str | None,
    location: str,
    genai_module=genai,
) -> object:
    """Return a cached Google Gen AI Vertex client."""
    if current_client is not None:
        return current_client
    if genai_module is None:
        raise RuntimeError("google-genai SDK is not installed")
    if not project:
        raise ValueError("VERTEX_PROJECT is not configured")
    client_factory = getattr(genai_module, "Client", None)
    if not callable(client_factory):
        raise RuntimeError("google.genai.Client is not available")
    return client_factory(vertexai=True, project=project, location=location)


def invoke_model(
    *,
    client: object,
    model: str,
    request,
    response_schema: dict[str, object],
    response_mime_type: str,
    timeout_s: float,
    types_module=types,
) -> object:
    """Invoke structured Gemini generation through Google Gen AI SDK."""
    if types_module is None:
        raise RuntimeError("google-genai SDK types are not installed")
    models = getattr(client, "models", None)
    generate_content = getattr(models, "generate_content", None)
    if not callable(generate_content):
        raise RuntimeError("google.genai client does not support generate_content")
    config = _build_generation_config(
        request=request,
        response_schema=response_schema,
        response_mime_type=response_mime_type,
        timeout_s=timeout_s,
        types_module=types_module,
    )
    return generate_content(
        model=model,
        contents=_build_user_content(request=request, types_module=types_module),
        config=config,
    )


def _build_generation_config(
    *,
    request,
    response_schema: dict[str, object],
    response_mime_type: str,
    timeout_s: float,
    types_module,
) -> object:
    """Build one typed structured-generation config with request timeout."""
    config_factory = getattr(types_module, "GenerateContentConfig", None)
    http_options_factory = getattr(types_module, "HttpOptions", None)
    if not callable(config_factory) or not callable(http_options_factory):
        raise RuntimeError("google-genai SDK typed generation config is not available")
    payload: dict[str, object] = {
        "response_mime_type": response_mime_type,
        "response_json_schema": response_schema,
        "http_options": http_options_factory(timeout=max(1, int(timeout_s * 1000))),
    }
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    return config_factory(**payload)


def _build_user_content(*, request, types_module) -> object:
    """Build text-only or multimodal Gemini content from transient inputs."""
    if not request.artifacts:
        return request.input
    part_cls = getattr(types_module, "Part", None)
    from_bytes = getattr(part_cls, "from_bytes", None)
    if not callable(from_bytes):
        raise RuntimeError("configured Google Gen AI SDK does not support multimodal artifact parts")
    return [
        request.input,
        *[
            from_bytes(data=artifact.payload, mime_type=artifact.content_type)
            for artifact in request.artifacts
        ],
    ]
