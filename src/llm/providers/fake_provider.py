from __future__ import annotations

import time
from typing import Any

from ..core.errors import ERROR_INVALID_OUTPUT, ERROR_RATE_LIMITED, ERROR_TIMEOUT
from ..core.request import LLMRequest
from ..core.result import LLMResult
from ..core.types import LLMError


class FakeProvider:
    provider_name = "fake"

    def __init__(
        self,
        *,
        task_outputs: dict[str, dict[str, Any]] | None = None,
        failing_tasks: dict[str, str] | None = None,
        default_model: str = "fake-model",
    ) -> None:
        self.task_outputs = task_outputs or {}
        self.failing_tasks = failing_tasks or {}
        self.default_model = default_model

    def generate(self, request: LLMRequest) -> LLMResult:
        started = time.perf_counter()

        failure_mode = self.failing_tasks.get(request.task)
        if failure_mode:
            return self._failed_result(failure_mode, request, started)

        output = self.task_outputs.get(request.task, {})
        text = output.get("text")
        json_payload = output.get("json")

        schema = request.structured_output.get("schema") if isinstance(request.structured_output, dict) else None
        if isinstance(schema, dict) and not self._is_schema_valid(schema, json_payload):
            return self._error_result(
                request=request,
                started=started,
                error_type=ERROR_INVALID_OUTPUT,
                message="Fake provider output failed schema validation",
                retriable=False,
            )

        return LLMResult(
            status="ok",
            text=text,
            structured_data=json_payload,
            provider=self.provider_name,
            model=self.default_model,
            latency_ms=int((time.perf_counter() - started) * 1000),
            retry_count=0,
            usage=None,
            error=None,
        )

    def _failed_result(self, failure_mode: str, request: LLMRequest, started: float) -> LLMResult:
        normalized = failure_mode.strip().lower()
        if normalized == ERROR_TIMEOUT:
            return self._error_result(request, started, ERROR_TIMEOUT, "Fake timeout", retriable=True)
        if normalized == ERROR_RATE_LIMITED:
            return self._error_result(request, started, ERROR_RATE_LIMITED, "Fake rate limited", retriable=True, http_status=429)
        return self._error_result(request, started, "unknown", f"Unknown fake failure mode: {failure_mode}", retriable=False)

    def _error_result(
        self,
        request: LLMRequest,
        started: float,
        error_type: str,
        message: str,
        retriable: bool,
        http_status: int | None = None,
    ) -> LLMResult:
        return LLMResult(
            status="error",
            text=None,
            structured_data=None,
            provider=self.provider_name,
            model=self.default_model,
            latency_ms=int((time.perf_counter() - started) * 1000),
            retry_count=request.max_retries,
            usage=None,
            error=LLMError(
                type=error_type,
                message_redacted=message,
                retriable=retriable,
                http_status=http_status,
            ),
        )

    def _is_schema_valid(self, schema: dict[str, Any], payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in payload:
                    return False

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return True

        for key, value in payload.items():
            expected = properties.get(key, {})
            expected_type = expected.get("type") if isinstance(expected, dict) else None
            if expected_type and not self._matches_type(value, expected_type):
                return False
        return True

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        py_type = type_map.get(expected_type)
        if py_type is None:
            return True
        return isinstance(value, py_type)
