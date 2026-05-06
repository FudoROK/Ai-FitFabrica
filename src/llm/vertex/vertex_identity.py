from __future__ import annotations

import json
from typing import Any


def build_vertex_identity_payload(
    *,
    raw_input: Any,
    request_context: dict[str, Any] | None,
    request_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    parsed_json: dict[str, Any] | None = None
    if isinstance(raw_input, str):
        candidate = raw_input.strip()
        if candidate.startswith("{"):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    parsed_json = parsed
            except json.JSONDecodeError:
                parsed_json = None

    user_text = ""
    context_payload: dict[str, Any] = {}
    message_payload: str | None = None
    if parsed_json:
        user_text = str(parsed_json.get("user_text") or "").strip()
        if _is_sales_runtime_envelope(parsed_json):
            backend_context = parsed_json.get("backend_context")
            if isinstance(backend_context, dict):
                context_payload = backend_context
            message_payload = candidate
        else:
            context = parsed_json.get("context")
            if isinstance(context, dict):
                context_payload = context
    if not user_text:
        user_text = str(raw_input or "")
    if not context_payload and isinstance(request_context, dict):
        context_payload = request_context

    identity = context_payload.get("identity") if isinstance(context_payload, dict) else None
    user_id = derive_user_id(identity=identity, metadata=request_metadata)
    session_id = derive_session_id(context=context_payload, metadata=request_metadata)

    return {
        "user_id": user_id,
        "session_id": session_id,
        "message": message_payload or user_text,
        "context": context_payload,
    }


def _is_sales_runtime_envelope(parsed_json: dict[str, Any]) -> bool:
    return (
        str(parsed_json.get("request_type") or "").strip() == "sales_dialog_turn"
        and isinstance(parsed_json.get("backend_context"), dict)
    )


def derive_user_id(*, identity: Any, metadata: dict[str, Any] | None) -> str:
    if isinstance(identity, dict):
        channel = str(identity.get("channel") or "telegram")
        external_user_id = identity.get("external_user_id")
        if external_user_id is not None:
            return f"{channel}:{external_user_id}"
        chat_id = identity.get("chat_id")
        if chat_id is not None:
            return f"{channel}:{chat_id}"
        lead_id = identity.get("lead_id")
        if lead_id:
            return str(lead_id)

    channel = str(metadata.get("channel") or "telegram") if isinstance(metadata, dict) else "telegram"
    lead_id = metadata.get("lead_id") if isinstance(metadata, dict) else None
    if lead_id:
        return str(lead_id)
    message_id = metadata.get("message_id") if isinstance(metadata, dict) else None
    if message_id:
        return f"{channel}:message:{message_id}"
    return f"{channel}:unknown"


def derive_session_id(*, context: dict[str, Any], metadata: dict[str, Any] | None) -> str | None:
    if isinstance(context, dict):
        session = context.get("session")
        if isinstance(session, dict):
            cached = session.get("vertex_session_id")
            if cached:
                return str(cached)
    provider_metadata = metadata.get("provider_metadata") if isinstance(metadata, dict) else None
    if isinstance(provider_metadata, dict):
        cached = provider_metadata.get("vertex_session_id")
        if cached:
            return str(cached)
    return None
