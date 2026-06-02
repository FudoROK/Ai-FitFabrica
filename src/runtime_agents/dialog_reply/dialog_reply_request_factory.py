from __future__ import annotations

import json
from typing import Any

from ...llm.contract_kinds import REPLY_AGENT_OUTPUT_KIND
from ...llm.tasks.helpers.task_request_builder import ProviderRequestParts
from ...llm.vertex.vertex_schema_builder import build_vertex_response_schema

_DIALOG_REPLY_RUNTIME_CONTRACT = """You are the backend-orchestrated dialog reply agent.

Hard rules:
- Treat backend context as authoritative runtime truth.
- If backend context contains prior messages, daily_summary, rolling_summary, active_window, conversation_state, or a known first_name, the client is not new.
- Do not greet the client as if this is the first conversation when prior interaction exists in backend context.
- Do not ask for the client's name again when backend context already knows first_name unless the user explicitly corrects it.
- Continue the current conversation from the known context instead of restarting discovery.
- Extract only lead_patch.first_name when the user's first name is explicitly stated in the current message.
- Do not invent any structured fields outside the schema.
- Return only data that matches the required JSON schema.
"""


def _build_runtime_input(*, user_text: str, context: dict[str, Any]) -> str:
    context_json = json.dumps(context, ensure_ascii=False, sort_keys=True)
    return (
        f"{_DIALOG_REPLY_RUNTIME_CONTRACT}\n\n"
        f"USER_MESSAGE:\n{user_text}\n\n"
        f"BACKEND_CONTEXT_JSON:\n{context_json}"
    )


def build_provider_request(payload: dict[str, Any]) -> ProviderRequestParts:
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    user_text = str(payload.get("user_text") or "").strip()
    runtime_input = _build_runtime_input(user_text=user_text, context=context)

    return ProviderRequestParts(
        model=payload["model"],
        instructions=_DIALOG_REPLY_RUNTIME_CONTRACT,
        input=runtime_input,
        context=context,
        structured_output={
            "kind": REPLY_AGENT_OUTPUT_KIND,
            "schema": build_vertex_response_schema(),
        },
        tool_capabilities=payload.get("tools") or [],
    )
