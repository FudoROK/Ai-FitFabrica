"""HTTP transport handlers for internal summary jobs and cron endpoints."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .payloads import (
    IngressBodyTooLargeError,
    IngressValidationError,
    MemorySummaryTaskRequest,
    parse_json_model,
    read_request_body_with_limit,
)
from .policies import verify_internal_oidc_bearer
from .runtime_dependencies import memory_summary_service, safe_memory_summary_response

logger = logging.getLogger(__name__)
router = APIRouter()
_SLA_MIN_INTERVAL_MINUTES = 5
_SLA_MAX_INTERVAL_MINUTES = 15
_last_scheduler_run_by_route: dict[str, datetime] = {}


def _log_scheduler_interval_health(*, route_name: str, as_of: datetime) -> None:
    previous_run_at = _last_scheduler_run_by_route.get(route_name)
    if previous_run_at is None:
        logger.info(
            "summary_scheduler_interval_initialized",
            extra={
                "route": route_name,
                "as_of": as_of.isoformat(),
                "expected_min_interval_minutes": _SLA_MIN_INTERVAL_MINUTES,
                "expected_max_interval_minutes": _SLA_MAX_INTERVAL_MINUTES,
            },
        )
        _last_scheduler_run_by_route[route_name] = as_of
        return

    elapsed_minutes = (as_of - previous_run_at).total_seconds() / 60.0
    reason_codes: list[str] = []
    if elapsed_minutes < _SLA_MIN_INTERVAL_MINUTES:
        reason_codes.append("interval_too_frequent")
    if elapsed_minutes > _SLA_MAX_INTERVAL_MINUTES:
        reason_codes.append("interval_too_slow_for_close_sla")

    log_extra = {
        "route": route_name,
        "as_of": as_of.isoformat(),
        "previous_run_at": previous_run_at.isoformat(),
        "elapsed_minutes": round(elapsed_minutes, 3),
        "expected_min_interval_minutes": _SLA_MIN_INTERVAL_MINUTES,
        "expected_max_interval_minutes": _SLA_MAX_INTERVAL_MINUTES,
        "reason_codes": reason_codes or ["interval_within_sla"],
    }
    if reason_codes:
        logger.warning("summary_scheduler_interval_out_of_sla", extra=log_extra)
    else:
        logger.info("summary_scheduler_interval_within_sla", extra=log_extra)
    _last_scheduler_run_by_route[route_name] = as_of


@router.post("/tasks/memory-summary")
async def memory_summary_task(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if not verify_internal_oidc_bearer(
        request,
        expected_audience=settings.memory_summary_task_auth_audience,
        allowed_service_accounts=settings.memory_summary_task_allowed_service_accounts,
        log_name="memory_summary_task_auth",
    ):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    try:
        body = await read_request_body_with_limit(request)
        payload = parse_json_model(body, MemorySummaryTaskRequest)
        lead_id = payload.lead_id
    except IngressBodyTooLargeError:
        return JSONResponse(status_code=413, content={"error": "payload_too_large"})
    except IngressValidationError:
        return JSONResponse(status_code=400, content={"error": "invalid_memory_summary_request"})

    try:
        if not lead_id:
            _log_scheduler_interval_health(
                route_name="/tasks/memory-summary",
                as_of=datetime.now(tz=timezone.utc),
            )
        # Transport passes orchestration inputs only; memory-day window resolution is domain/service-owned.
        result = await memory_summary_service(settings).build_memory_summary_for_lead(lead_id=lead_id)
        if result.errors:
            logger.warning(
                "memory_summary_task_completed_with_errors",
                extra={"lead_id": lead_id, "error_count": result.error_count, "errors": result.errors},
            )
        if not lead_id:
            return JSONResponse(
                status_code=200,
                content={
                    "pipeline_status": "failed" if result.outcome_counts.get("failed", 0) > 0 else "completed",
                    "mode": "batch",
                    "total_selected": result.total_selected,
                    "total_processed": result.total_processed,
                    "total_succeeded": result.total_succeeded,
                    "total_failed": result.total_failed,
                    "failed": result.failed_leads,
                    "outcomes": dict(result.outcome_counts),
                    "reason_codes": dict(result.reason_code_counts),
                },
            )
        return JSONResponse(status_code=200, content=safe_memory_summary_response(result=result))
    except Exception:
        logger.exception("Memory summary task failed")
        return JSONResponse(status_code=500, content={"error": "memory_summary_failed"})
