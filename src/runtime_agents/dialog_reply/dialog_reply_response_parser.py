from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from ...llm.core.result import LLMResult as CoreLLMResult
from ...llm.tasks.helpers.task_request_builder import ensure_ok_result
from .dialog_reply_response_mapper import build_parsed_payload_diagnostic
from .dialog_reply_runtime_schemas import DialogReplyRuntimeOutput
from .dialog_reply_semantic_validator import validate_runtime_semantics

logger = logging.getLogger(__name__)


def parse_provider_response(result: CoreLLMResult) -> dict[str, Any]:
    ready = ensure_ok_result(result)
    if not isinstance(ready.structured_data, dict):
        logger.warning(
            "LLM_REPLY_STRUCTURED_PAYLOAD_MISSING",
            extra={"status": "invalid_output", "provider": ready.provider},
        )
        raise ValueError("invalid_output: structured payload is missing")

    typed_output = _parse_strict_runtime_output(ready.structured_data)
    _log_parsed_payload_diagnostic(typed_output)
    logger.info("LLM_REPLY_PARSED", extra={"status": "ok"})
    return typed_output.model_dump(mode="python")


def _parse_strict_runtime_output(payload: dict[str, Any]) -> DialogReplyRuntimeOutput:
    try:
        typed_output = DialogReplyRuntimeOutput.model_validate(payload)
    except ValidationError as exc:
        logger.warning("LLM_REPLY_SCHEMA_INVALID", extra={"status": "invalid_output", "reason": str(exc)})
        raise ValueError(f"invalid_output: {exc}") from exc

    semantic_ok, semantic_reason = validate_runtime_semantics(typed_output)
    if not semantic_ok:
        logger.warning(
            "LLM_REPLY_SEMANTIC_INVALID",
            extra={"status": "invalid_output", "reason": semantic_reason},
        )
        raise ValueError(f"invalid_output: {semantic_reason}")

    return typed_output


def _log_parsed_payload_diagnostic(payload: DialogReplyRuntimeOutput) -> None:
    logger.info(
        "LLM_REPLY_PARSED_DIAGNOSTIC %s",
        build_parsed_payload_diagnostic(
            reply_text=payload.reply_text,
            system_payload=payload.system_payload,
        ),
    )
