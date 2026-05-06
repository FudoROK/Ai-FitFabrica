from __future__ import annotations

from pydantic import ValidationError

from ...llm.core.result import LLMResult as CoreLLMResult
from ...llm.tasks.helpers.task_request_builder import ensure_ok_result
from .contracts.daily import DailyMemoryContract
from .contracts.rolling import RollingMemoryContract
from .memory_response_mapper import map_runtime_payload


def _ensure_payload(result: CoreLLMResult, *, boundary_error_code: str) -> dict[str, object]:
    ready = ensure_ok_result(result)
    if not isinstance(ready.structured_data, dict):
        raise ValueError(f"{boundary_error_code}: structured payload is missing")
    runtime_payload = map_runtime_payload(ready.structured_data)
    if "memory_payload" in runtime_payload:
        raise ValueError(f"{boundary_error_code}: legacy wrapper payload is forbidden")
    return runtime_payload


def parse_daily_provider_response(result: CoreLLMResult) -> dict[str, object]:
    runtime_payload = _ensure_payload(result, boundary_error_code="daily_contract_invalid")
    try:
        typed_output = DailyMemoryContract.model_validate(runtime_payload)
    except ValidationError as exc:
        raise ValueError(f"daily_contract_invalid: {exc}") from exc
    return typed_output.model_dump(mode="python", exclude_none=True)


def parse_rolling_provider_response(result: CoreLLMResult) -> dict[str, object]:
    runtime_payload = _ensure_payload(result, boundary_error_code="rolling_contract_invalid")
    try:
        typed_output = RollingMemoryContract.model_validate(runtime_payload)
    except ValidationError as exc:
        raise ValueError(f"rolling_contract_invalid: {exc}") from exc
    return typed_output.model_dump(mode="python", exclude_none=True)


def parse_provider_response(result: CoreLLMResult) -> dict[str, object]:
    return parse_daily_provider_response(result)
