from __future__ import annotations

from typing import Any

from src.llm.reply_task_contract import REPLY_RUNTIME_TASKS


def resolve_contract_kind(request, structured_output: dict[str, Any] | None) -> str:
    name = structured_output.get("name") if isinstance(structured_output, dict) else None
    if isinstance(name, str) and name.strip():
        return name.strip()
    return request.task


def resolve_response_schema(
    *,
    request,
    build_error_result,
    build_vertex_response_schema,
    started: float,
    retry_count: int,
    model: str,
    provider_name: str,
) -> dict[str, Any]:
    structured_output = request.structured_output if isinstance(request.structured_output, dict) else None
    schema = structured_output.get("schema") if structured_output else None
    contract_kind = resolve_contract_kind(request, structured_output)

    if isinstance(schema, dict):
        return {"response_schema": schema, "contract_kind": contract_kind, "error_result": None}
    if request.task in REPLY_RUNTIME_TASKS:
        return {"response_schema": build_vertex_response_schema(), "contract_kind": contract_kind, "error_result": None}
    return {
        "response_schema": {},
        "contract_kind": contract_kind,
        "error_result": build_error_result(
            started=started,
            retry_count=retry_count,
            model=model,
            provider_name=provider_name,
            error_type="bad_request",
            message=(
                "Structured output schema is required: request.structured_output must be a dict "
                f"containing a dict schema for task '{request.task}'."
            ),
            retriable=False,
            http_status=400,
        ),
    }
