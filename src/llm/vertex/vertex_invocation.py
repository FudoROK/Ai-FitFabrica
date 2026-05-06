# src/llm/vertex/vertex_invocation.py
from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

from ..contract_kinds import canonicalize_contract_kind
from ..vertex.vertex_parser import (
    collect_output_from_events,
    event_preview,
    is_memory_contract_kind,
    resolve_contract_selector,
    selector_mode_name,
)
from ..vertex.vertex_session import resolve_session

_EVENT_PREVIEW_LIMIT = 12


def invoke_session_flow(
    *,
    client: Any,
    agent_resource: str,
    user_id: str,
    incoming_session_id: str | None,
    message: str,
    context: dict[str, Any],
    structured_contract: dict[str, Any] | None,
    correlation_id: str | None,
    timeout_s: float,
    logger: Any,
) -> dict[str, Any]:
    started = time.perf_counter()

    session_id, session_created = resolve_session(
        client=client,
        user_id=user_id,
        incoming_session_id=incoming_session_id,
        logger=logger,
    )

    stream_result = run_stream_query(
        client=client,
        user_id=user_id,
        session_id=session_id,
        message=message,
        context=context,
        structured_contract=structured_contract,
        correlation_id=correlation_id,
        logger=logger,
    )
    events = stream_result["events"]

    elapsed = time.perf_counter() - started
    if elapsed > timeout_s:
        raise TimeoutError(f"Vertex reasoning engine stream exceeded timeout: {elapsed:.2f}s > {timeout_s:.2f}s")

    contract_kind = canonicalize_contract_kind(structured_contract.get("kind")) if isinstance(structured_contract, dict) else None
    selector = resolve_contract_selector(contract_kind=contract_kind)
    selected_mode = selector_mode_name(contract_kind=contract_kind)
    parsed = collect_output_from_events(
        events,
        contract_selector=selector,
        contract_kind=contract_kind,
        correlation_id=correlation_id,
    )
    if is_memory_contract_kind(contract_kind):
        logger.info(
            "MEMORY_CONTRACT_SELECTOR_OUTCOME",
            extra={
                "correlation_id": correlation_id,
                "selector_mode": selected_mode,
                "event_count": len(events),
                "output_is_dict": isinstance(parsed.get("output"), dict),
            },
        )
    parsed["session_id"] = session_id
    parsed["session_created"] = session_created
    parsed["structured_mode"] = stream_result["structured_mode"]
    parsed["structured_requested"] = stream_result["structured_requested"]
    parsed["structured_contract_kind"] = stream_result["structured_contract_kind"]
    parsed["structured_contract_required"] = stream_result["structured_contract_required"]
    parsed["structured_enforced"] = stream_result["structured_enforced"]

    logger.info(
        "VERTEX_AGENT_INVOCATION_SUCCESS",
        extra={
            "vertex_agent_resource": agent_resource,
            "user_id": user_id,
            "session_id": session_id,
            "session_created": session_created,
            "event_count": parsed["event_count"],
            "structured_mode": parsed["structured_mode"],
            "structured_requested": parsed["structured_requested"],
            "structured_contract_kind": parsed["structured_contract_kind"],
            "structured_contract_required": parsed["structured_contract_required"],
            "structured_enforced": parsed["structured_enforced"],
            "structured_payload_keys": list(parsed["output"].keys()) if isinstance(parsed["output"], dict) else [],
            "correlation_id": correlation_id,
        },
    )
    return parsed


def run_stream_query(
    *,
    client: Any,
    user_id: str,
    session_id: str,
    message: str,
    context: dict[str, Any],
    structured_contract: dict[str, Any] | None,
    correlation_id: str | None,
    logger: Any,
) -> dict[str, Any]:
    structured_contract = structured_contract if isinstance(structured_contract, dict) else None
    structured_requested = structured_contract is not None
    contract_kind = canonicalize_contract_kind(structured_contract.get("kind")) if structured_contract else None
    available_methods = list_supported_invocation_methods(client)
    logger.info(
        "VERTEX_AGENT_STREAM_QUERY_START",
        extra={
            "user_id": user_id,
            "session_id": session_id,
            "available_methods": available_methods,
            "structured_requested": structured_requested,
            "structured_contract_kind": contract_kind,
            "structured_contract_required": bool(structured_contract and structured_contract.get("required")),
            "correlation_id": correlation_id,
            "context_keys": sorted(context.keys()) if isinstance(context, dict) else [],
            "has_context_payload": bool(context),
        },
    )

    selected_method, selected_callable = select_invocation_method(
        client,
        available_methods,
        structured_contract=structured_contract,
    )
    call_kwargs: dict[str, Any] = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message,
    }
    transport_mode = "message_only"
    transport_context_omitted_reason = None
    if context:
        transport_context_omitted_reason = "agent_engine_runtime_incompatible"

    logger.info(
        "VERTEX_AGENT_TRANSPORT_PAYLOAD",
        extra={
            "user_id": user_id,
            "session_id": session_id,
            "selected_method": selected_method,
            "transport_mode": transport_mode,
            "message_len": len(message),
            "context_payload": context if context else {},
            "transport_context_omitted_reason": transport_context_omitted_reason,
        },
    )
    structured_mode = "disabled"
    structured_enforced = False
    response = selected_callable(**call_kwargs)
    if asyncio.iscoroutine(response):
        response = run_coroutine(response)

    if selected_method in ("query", "async_query"):
        events = [response]
    else:
        events = response

    if hasattr(events, "__aiter__"):
        events = run_coroutine(collect_async_events(events))
    elif not isinstance(events, list):
        events = list(events)

    logger.info(
        "VERTEX_AGENT_STREAM_QUERY_DONE",
        extra={
            "user_id": user_id,
            "session_id": session_id,
            "selected_method": selected_method,
            "structured_mode": structured_mode,
            "structured_requested": structured_requested,
            "structured_contract_kind": contract_kind,
            "structured_contract_required": bool(structured_contract and structured_contract.get("required")),
            "structured_enforced": structured_enforced,
            "event_count": len(events),
            "event_preview": [event_preview(evt) for evt in events[:_EVENT_PREVIEW_LIMIT]],
            "correlation_id": correlation_id,
            "transport_mode": transport_mode,
            "transport_context_omitted_reason": transport_context_omitted_reason,
        },
    )
    return {
        "events": events,
        "structured_mode": structured_mode,
        "structured_requested": structured_requested,
        "structured_contract_kind": contract_kind,
        "structured_contract_required": bool(structured_contract and structured_contract.get("required")),
        "structured_enforced": structured_enforced,
        "transport_mode": transport_mode,
        "transport_context_omitted_reason": transport_context_omitted_reason,
    }


def select_invocation_method(
    client: Any,
    available_methods: list[str],
    *,
    structured_contract: dict[str, Any] | None,
) -> tuple[str, Any]:
    ordered_candidates: list[tuple[str, Any]] = []
    _ = structured_contract
    for method_name in ("async_stream_query", "stream_query", "query", "async_query"):
        method = getattr(client, method_name, None)
        if callable(method):
            ordered_candidates.append((method_name, method))

    if ordered_candidates:
        return ordered_candidates[0]

    raise RuntimeError(
        "ReasoningEngine client does not support second-step invocation "
        f"(available_methods={available_methods})"
    )


def list_supported_invocation_methods(client: Any) -> list[str]:
    candidates = ["create_session", "get_session", "async_query", "async_stream_query", "stream_query", "query"]
    return [name for name in candidates if callable(getattr(client, name, None))]


def run_coroutine(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    container: dict[str, Any] = {}

    def _runner() -> None:
        try:
            container["result"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001
            container["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in container:
        raise container["error"]
    return container.get("result")


async def collect_async_events(async_events: Any) -> list[Any]:
    out = []
    async for event in async_events:
        out.append(event)
    return out
