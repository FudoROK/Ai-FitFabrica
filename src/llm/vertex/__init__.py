from __future__ import annotations

__all__ = [
    "build_error_result",
    "classify_provider_exception",
    "build_vertex_identity_payload",
    "derive_session_id",
    "derive_user_id",
    "invoke_session_flow",
    "collect_output_from_events",
    "resolve_contract_selector",
    "VertexProvider",
    "build_vertex_response_schema",
    "validate_agent_output",
    "validate_against_schema",
    "extract_session_id",
    "get_client",
    "resolve_session",
]


def __getattr__(name: str):
    """Avoid importing the full Vertex provider stack for lightweight schema/runtime helpers."""
    if name in {"build_error_result", "classify_provider_exception"}:
        from .vertex_errors import build_error_result, classify_provider_exception

        return {
            "build_error_result": build_error_result,
            "classify_provider_exception": classify_provider_exception,
        }[name]
    if name in {"build_vertex_identity_payload", "derive_session_id", "derive_user_id"}:
        from .vertex_identity import build_vertex_identity_payload, derive_session_id, derive_user_id

        return {
            "build_vertex_identity_payload": build_vertex_identity_payload,
            "derive_session_id": derive_session_id,
            "derive_user_id": derive_user_id,
        }[name]
    if name == "invoke_session_flow":
        from .vertex_invocation import invoke_session_flow

        return invoke_session_flow
    if name in {"collect_output_from_events", "resolve_contract_selector"}:
        from .vertex_parser import collect_output_from_events, resolve_contract_selector

        return {
            "collect_output_from_events": collect_output_from_events,
            "resolve_contract_selector": resolve_contract_selector,
        }[name]
    if name == "VertexProvider":
        from .vertex_provider import VertexProvider

        return VertexProvider
    if name == "build_vertex_response_schema":
        from .vertex_schema_builder import build_vertex_response_schema

        return build_vertex_response_schema
    if name in {"validate_agent_output", "validate_against_schema"}:
        from .vertex_schema_validator import validate_agent_output, validate_against_schema

        return {
            "validate_agent_output": validate_agent_output,
            "validate_against_schema": validate_against_schema,
        }[name]
    if name in {"extract_session_id", "get_client", "resolve_session"}:
        from .vertex_session import extract_session_id, get_client, resolve_session

        return {
            "extract_session_id": extract_session_id,
            "get_client": get_client,
            "resolve_session": resolve_session,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
