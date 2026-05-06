from __future__ import annotations

from typing import Any


def get_client(*, cached_client: Any, reasoning_engines: Any, agent_resource: str | None) -> Any:
    if cached_client is not None:
        return cached_client
    if reasoning_engines is None:
        raise RuntimeError("vertexai SDK is not installed")
    if hasattr(reasoning_engines, "get"):
        return reasoning_engines.get(agent_resource)
    if hasattr(reasoning_engines, "ReasoningEngine"):
        return reasoning_engines.ReasoningEngine(agent_resource)
    raise RuntimeError("vertexai reasoning_engines API is not supported")


def resolve_session(
    *,
    client: Any,
    user_id: str,
    incoming_session_id: str | None,
    logger: Any,
) -> tuple[str, bool]:
    if incoming_session_id:
        logger.info(
            "VERTEX_AGENT_SESSION_REUSE_REQUESTED",
            extra={"user_id": user_id, "session_id": incoming_session_id},
        )
        get_session = getattr(client, "get_session", None)
        if callable(get_session):
            try:
                existing = get_session(user_id=user_id, session_id=incoming_session_id)
                resolved = extract_session_id(existing) or incoming_session_id
                logger.info(
                    "VERTEX_AGENT_SESSION_REUSED",
                    extra={"user_id": user_id, "session_id": resolved},
                )
                return resolved, False
            except Exception:
                logger.warning(
                    "VERTEX_AGENT_SESSION_REUSE_FAILED_FALLBACK_CREATE",
                    extra={"user_id": user_id, "session_id": incoming_session_id},
                    exc_info=True,
                )

    create_session = getattr(client, "create_session", None)
    if not callable(create_session):
        raise RuntimeError("ReasoningEngine client does not support create_session")
    created = create_session(user_id=user_id)
    session_id = extract_session_id(created)
    if not session_id:
        raise ValueError("Vertex create_session response did not include session_id")

    logger.info(
        "VERTEX_AGENT_SESSION_CREATED",
        extra={"user_id": user_id, "session_id": session_id},
    )
    return session_id, True


def extract_session_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "session_id", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
        return None
    for attr in ("id", "session_id", "name"):
        candidate = getattr(value, attr, None)
        if isinstance(candidate, str) and candidate:
            return candidate
    if hasattr(value, "to_dict"):
        dumped = value.to_dict()
        if isinstance(dumped, dict):
            return extract_session_id(dumped)
    return None
