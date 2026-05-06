"""HTTP transport handlers for health and status endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .policies import is_status_endpoint_request_authorized

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    if not is_status_endpoint_request_authorized(request, settings):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return JSONResponse(status_code=200, content={"status": "healthy"})


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
