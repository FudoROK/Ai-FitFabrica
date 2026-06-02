from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from ...llm.profiles import ProfileRegistry, SemanticValidationContext
from ...llm import LLMMeta
from ...services.runtime.feature_flags import FeatureFlags, resolve_feature_flags

logger = logging.getLogger(__name__)


class GenerateReplyUseCase:
    def __init__(
        self,
        llm_service,
        *,
        profile_registry: ProfileRegistry | None = None,
        feature_flags: FeatureFlags | None = None,
    ) -> None:
        self.llm_service = llm_service
        self.profile_registry = profile_registry or ProfileRegistry()
        self.feature_flags = feature_flags or resolve_feature_flags()

    async def execute(self, *, message: dict, channel: str, lead_id: str | None, text: str, llm_context: dict):
        normalized_context = _normalize_for_json(llm_context)
        runtime_envelope = _build_primary_runtime_envelope(user_text=text, backend_context=normalized_context)
        raw_input = json.dumps(runtime_envelope, ensure_ascii=False)
        logger.info(
            "LLM_CONTEXT_BUILT",
            extra={
                "task": "dialog_reply_task",
                "channel": channel,
                "lead_id": lead_id,
                "user_text": text,
                "context_payload": normalized_context,
                "runtime_envelope_summary": {
                    "request_type": runtime_envelope["request_type"],
                    "contract_version": runtime_envelope["contract_version"],
                    "top_level_keys": sorted(runtime_envelope.keys()),
                    "backend_context_keys": sorted(normalized_context.keys()) if isinstance(normalized_context, dict) else [],
                },
                "context_summary": {
                    "top_level_keys": sorted(normalized_context.keys()) if isinstance(normalized_context, dict) else [],
                    "has_lead_snapshot": bool(normalized_context.get("lead_snapshot")) if isinstance(normalized_context, dict) else False,
                    "has_memory": bool(normalized_context.get("memory")) if isinstance(normalized_context, dict) else False,
                    "memory_last_messages_count": len((normalized_context.get("memory") or {}).get("last_messages") or [])
                    if isinstance(normalized_context, dict)
                    else 0,
                    "has_rolling_summary": bool((normalized_context.get("memory") or {}).get("rolling_summary"))
                    if isinstance(normalized_context, dict)
                    else False,
                    "has_daily_summary": bool((normalized_context.get("memory") or {}).get("daily_summary"))
                    if isinstance(normalized_context, dict)
                    else False,
                },
            },
        )
        result = await self.llm_service.run(
            task="dialog_reply_task",
            payload={
                "user_text": text,
                "context": normalized_context,
                "runtime_envelope": runtime_envelope,
                "input": raw_input,
            },
            meta=LLMMeta(
                message_id=str(message.get("message_id")) if message.get("message_id") is not None else None,
                channel=channel,
                lead_id=lead_id,
            ),
        )
        data = result.data or {}
        logger.info(
            "reply_profile_runtime_decision",
            extra={"enabled": self.feature_flags.reply_runtime_enabled()},
        )
        if not self.feature_flags.reply_runtime_enabled():
            logger.info("reply_profile_runtime_disabled_fallback")
            reply_text = str(data.get("reply_text") or "").strip()
            system_payload = data.get("system_payload")
            logger.info(
                "reply_profile_extraction",
                extra={"status": "success" if reply_text else "extraction_not_found"},
            )
            reply_meta = _extract_reply_meta(data, getattr(result, "provider_metadata", None))
            return result, reply_text, system_payload, reply_meta

        reply_profile = self.profile_registry.get_profile(flow="dialog_reply_task")
        logger.info("reply_profile_registry_selected", extra={"profile": type(reply_profile).__name__})
        typed_output = reply_profile.parse(data)
        logger.info("reply_profile_extraction", extra={"status": "success"})
        validation = reply_profile.validate(typed_output)
        semantic = reply_profile.semantic_validate(
            typed_output,
            SemanticValidationContext(payload={"channel": channel, "lead_id": lead_id or ""}),
        )
        if not validation.ok:
            logger.warning("reply_profile_contract_validation", extra={"status": "contract_invalid"})
            result.ok = False
            result.error = {"kind": "contract_invalid", "message": "reply_profile_validation_failed"}
            reply_text = ""
            system_payload = None
        elif not semantic.ok:
            logger.warning("reply_profile_semantic_validation", extra={"status": "semantic_invalid"})
            result.ok = False
            result.error = {"kind": "semantic_invalid", "message": "reply_profile_semantic_validation_failed"}
            reply_text = ""
            system_payload = None
        else:
            logger.info("reply_profile_contract_validation", extra={"status": "pass"})
            logger.info("reply_profile_semantic_validation", extra={"status": "pass"})
            reply_text = typed_output.reply_text
            system_payload = typed_output.system_payload
        reply_meta = _extract_reply_meta(data, getattr(result, "provider_metadata", None))
        return result, reply_text, system_payload, reply_meta


def _normalize_for_json(value: Any):
    if isinstance(value, dict):
        return {key: _normalize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _build_primary_runtime_envelope(*, user_text: str, backend_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_type": "primary_dialog_turn",
        "contract_version": "primary_runtime_envelope_v1",
        "user_text": user_text,
        "backend_context": backend_context,
    }


def _extract_reply_meta(data: dict[str, Any], provider_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    provider_session_id = None

    session_data = data.get("session")
    if isinstance(session_data, dict):
        provider_session_id = session_data.get("provider_session_id")

    if not provider_session_id and isinstance(provider_metadata, dict):
        provider_session_id = provider_metadata.get("vertex_session_id")

    if not provider_session_id:
        return {}

    return {"provider_session_id": str(provider_session_id)}
