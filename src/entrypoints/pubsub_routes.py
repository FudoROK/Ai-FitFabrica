"""HTTP transport handlers for Pub/Sub push delivery."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .payloads import (
    IngressBodyTooLargeError,
    IngressValidationError,
    PubSubPushRequest,
    decode_pubsub_payload,
    parse_json_model,
    read_request_body_with_limit,
)
from .policies import verify_pubsub_oidc_jwt
from .pubsub_pipeline import process_pubsub_normalized_event
from .runtime_dependencies import dialog_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/pubsub")
async def pubsub_push(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if not verify_pubsub_oidc_jwt(request, settings):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    try:
        body = await read_request_body_with_limit(request)
        push_request = parse_json_model(body, PubSubPushRequest)
        normalized = decode_pubsub_payload(push_request)
    except IngressBodyTooLargeError:
        return JSONResponse(status_code=413, content={"error": "payload_too_large"})
    except IngressValidationError:
        return JSONResponse(status_code=400, content={"error": "invalid_pubsub_message"})

    outcome = await process_pubsub_normalized_event(
        normalized=normalized,
        handle_message=dialog_service(settings).handle_normalized_message,
    )
    if outcome.kind == "invalid_idempotency_key":
        return JSONResponse(status_code=400, content={"error": "invalid_idempotency_key"})
    if outcome.kind == "idempotency_unavailable":
        return JSONResponse(status_code=500, content={"error": "idempotency_unavailable"})
    if outcome.kind == "duplicate_skipped":
        logger.warning("PUBSUB_DUPLICATE_SKIPPED", extra={"status": "duplicate", "task": "dialog_reply"})
        return JSONResponse(status_code=200, content={"status": "duplicate_skipped", "pipeline_status": "success"})
    if outcome.kind == "already_processing":
        logger.warning("PUBSUB_ALREADY_PROCESSING", extra={"status": "partial", "task": "dialog_reply"})
        return JSONResponse(status_code=409, content={"status": "already_processing", "pipeline_status": "partial"})
    if outcome.kind == "dialog_failed":
        return JSONResponse(status_code=500, content={"error": "dialog_failed", "pipeline_status": "failed"})

    return JSONResponse(status_code=200, content={"status": "ok", "pipeline_status": outcome.pipeline_status})
