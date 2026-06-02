from __future__ import annotations

from typing import Any

from ...llm.core.result import LLMResult as CoreLLMResult
from ...llm.tasks.helpers.task_request_builder import ProviderRequestParts
from .dialog_reply_request_factory import build_provider_request as _build_provider_request
from .dialog_reply_response_parser import parse_provider_response as _parse_provider_response


def build_provider_request(payload: dict[str, Any], _meta: Any) -> ProviderRequestParts:
    return _build_provider_request(payload)


def parse_provider_response(result: CoreLLMResult) -> dict[str, Any]:
    return _parse_provider_response(result)
