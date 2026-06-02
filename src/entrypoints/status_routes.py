"""HTTP transport handlers for health and status endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .runtime_dependencies import operations_runtime_dependencies
from .policies import is_status_endpoint_request_authorized
from src.use_cases.try_on.activation_probe import probe_try_on_real_activation

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if not is_status_endpoint_request_authorized(request, settings):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    operations_health = await operations_runtime_dependencies(settings).health_service.snapshot()
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "infrastructure": {
                "postgresql": "configured" if settings.postgres_dsn else "not_configured",
                "redis": "configured" if settings.redis_url else "not_configured",
                "object_storage": settings.object_storage_backend,
                "qdrant": "configured" if settings.qdrant_url else "not_configured",
            },
            "operations": operations_health.model_dump(mode="json"),
            "try_on_real_activation": probe_try_on_real_activation(settings).model_dump(mode="json"),
        },
    )


@router.get("/time")
async def time_check(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if not is_status_endpoint_request_authorized(request, settings):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    now_utc = datetime.now(timezone.utc)
    try:
        now_local = now_utc.astimezone(ZoneInfo("Asia/Almaty"))
    except Exception:
        now_local = now_utc
    return JSONResponse(status_code=200, content={"utc": now_utc.isoformat(), "local": now_local.isoformat()})
