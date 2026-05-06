"""HTTP transport handlers for Telegram webhook ingress."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.domain.normalized_ingress_event import build_ingress_rate_key
from ..adapters.messaging.telegram.telegram_handler import normalize_telegram_update
from ..services.pubsub.pubsub_service import publish_normalized_update
from ..utils.log_redaction import hash_chat_id
from .payloads import (
    IngressBodyTooLargeError,
    IngressValidationError,
    TelegramWebhookRequest,
    parse_json_model,
    read_request_body_with_limit,
)
from .policies import has_valid_token
from .runtime_dependencies import ingress_global_safety_limiter, ingress_rate_limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if not has_valid_token(request, settings.telegram_webhook_secret, "X-Telegram-Bot-Api-Secret-Token"):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    try:
        body = await read_request_body_with_limit(request)
        update = parse_json_model(body, TelegramWebhookRequest)
    except IngressBodyTooLargeError:
        return JSONResponse(status_code=413, content={"error": "payload_too_large"})
    except IngressValidationError:
        return JSONResponse(status_code=400, content={"error": "invalid_telegram_payload"})

    update_id = update.update_id
    message = update.message or update.edited_message
    chat_id = message.chat.id if message else None

    logger.info(
        "WEBHOOK_RECEIVED",
        extra={
            "telegram_update_id": update_id,
            "chat_id_hash": hash_chat_id(chat_id),
            "status": "received",
            "task": "dialog_reply",
            "update_kind": update.update_kind,
        },
    )

    if message is None:
        return JSONResponse(status_code=200, content={"status": "ignored", "reason": "unsupported_update_kind"})

    try:
        normalized = normalize_telegram_update(update)
    except Exception:
        logger.exception("Failed to normalize Telegram update")
        return JSONResponse(status_code=200, content={"status": "ignored"})

    ingress_rate_key = build_ingress_rate_key(normalized)
    ingress_decision = ingress_rate_limiter(settings).allow(ingress_rate_key)
    if ingress_decision.status == "denied_limit_exceeded":
        logger.warning(
            "INGRESS_RATE_LIMIT_DENIED",
            extra={"channel": normalized.channel, "reason": ingress_decision.reason},
        )
        return JSONResponse(
            status_code=429,
            content={
                "status": "rate_limited",
                "reason": "ingress_source_rate_limit_exceeded",
                "pipeline_status": "failed",
                "retry_after_seconds": ingress_decision.retry_after_seconds,
            },
        )
    elif ingress_decision.status == "backend_error":
        # Fail-open: continue processing, log error
        logger.error(
            "RATE_LIMIT_BACKEND_FAILURE",
            extra={
                "channel": normalized.channel,
                "reason": ingress_decision.reason,
                "fail_mode": "open",  # Explicitly state fail-open
            },
        )
        # Continue to global safety limiter and then Pub/Sub as if allowed

    global_decision = ingress_global_safety_limiter(settings).allow("ingress:global")
    if global_decision.status == "denied_limit_exceeded":
        logger.warning("INGRESS_GLOBAL_SAFETY_CAP_DENIED", extra={"reason": global_decision.reason})
        return JSONResponse(
            status_code=429,
            content={
                "status": "rate_limited",
                "reason": "ingress_global_safety_cap_exceeded",
                "pipeline_status": "failed",
                "retry_after_seconds": global_decision.retry_after_seconds,
            },
        )
    elif global_decision.status == "backend_error":
        logger.error(
            "RATE_LIMIT_BACKEND_FAILURE",
            extra={
                "channel": normalized.channel, # Assuming normalized is available here
                "reason": global_decision.reason,
                "fail_mode": "open",
            },
        )
        # Continue as if allowed

    try:
        publish_normalized_update(normalized.model_dump(), topic=settings.pubsub_topic_name, project_id=settings.gcp_project_id)
    except Exception:  # pragma: no cover - network
        logger.exception("PUBSUB_PUBLISH_FAILED", extra={"task": "dialog_reply", "status": "failed"})
        return JSONResponse(status_code=503, content={"status": "enqueue_failed", "pipeline_status": "failed"})

    return JSONResponse(status_code=200, content={"status": "queued", "pipeline_status": "success"})
