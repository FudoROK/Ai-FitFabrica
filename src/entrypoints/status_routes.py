"""HTTP transport handlers for health and status endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .runtime_dependencies import operations_runtime_dependencies
from .policies import is_status_endpoint_request_authorized
from src.use_cases.try_on.activation_probe import probe_try_on_real_activation

router = APIRouter()


class ReadinessService(BaseModel):
    """Configuration-level readiness for one backend-owned dependency."""

    status: Literal["configured", "ready", "blocked", "disabled"]
    detail: str


class NoBillingReadinessResponse(BaseModel):
    """Safe readiness report for work that can continue before billing is restored."""

    ok: bool
    mode: Literal["no_billing_preparation"]
    services: dict[str, ReadinessService]
    blockers: list[str]
    safe_without_billing: list[str]
    post_billing_checks: list[str]


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


@router.get("/ready", response_model=NoBillingReadinessResponse)
async def readiness_check(request: Request) -> NoBillingReadinessResponse | JSONResponse:
    """Return no-billing project readiness without calling paid external providers."""

    settings = request.app.state.settings
    if not is_status_endpoint_request_authorized(request, settings):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return build_no_billing_readiness(settings)


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


def build_no_billing_readiness(settings: object) -> NoBillingReadinessResponse:
    """Build a deterministic readiness map from configuration only."""

    services = {
        "sql": _sql_status(settings),
        "redis": _redis_status(settings),
        "object_storage": _object_storage_status(settings),
        "qdrant": _qdrant_status(settings),
        "auth": _auth_status(settings),
        "billing": _billing_status(settings),
        "ai_provider": _ai_provider_status(settings),
        "image_editing": _image_editing_status(settings),
        "search_engine_discovery": _search_engine_discovery_status(settings),
        "admin_surface": _admin_surface_status(settings),
    }
    blockers = _readiness_blockers(services)
    return NoBillingReadinessResponse(
        ok=not blockers,
        mode="no_billing_preparation",
        services=services,
        blockers=blockers,
        safe_without_billing=[
            "public_demo_request_capture",
            "auth_fail_closed_contract",
            "admin_candidate_review_contracts",
            "business_catalog_admin_review",
            "taxonomy_admin_review",
            "deterministic_try_on_sandbox",
            "frontend_workspace_shell_smoke",
        ],
        post_billing_checks=[
            "restore_billing_provider_and_credit_ledger_gate",
            "enable_production_auth_provider",
            "run_paid_try_on_activation_probe",
            "verify_sql_redis_object_storage_qdrant_connectivity",
            "run_end_to_end_credit_charge_and_refund_flow",
        ],
    )


def _readiness_blockers(services: dict[str, ReadinessService]) -> list[str]:
    """Collect only blockers that must be cleared before full paid testing."""

    blocker_codes = {
        "auth": "admin_auth_not_configured",
        "billing": "billing_core_not_enabled",
        "ai_provider": "ai_provider_not_production_ready",
        "image_editing": "image_editing_provider_not_production_ready",
        "search_engine_discovery": "search_engine_discovery_not_configured",
    }
    return [code for name, code in blocker_codes.items() if services[name].status == "blocked"]


def _sql_status(settings: object) -> ReadinessService:
    """Report whether PostgreSQL persistence is configured."""

    if _configured(_setting(settings, "postgres_dsn")):
        return ReadinessService(status="configured", detail="PostgreSQL DSN is configured.")
    return ReadinessService(status="disabled", detail="PostgreSQL DSN is not configured for this runtime.")


def _redis_status(settings: object) -> ReadinessService:
    """Report whether Redis-backed coordination is configured."""

    if _configured(_setting(settings, "redis_url")):
        return ReadinessService(status="configured", detail="Redis URL is configured.")
    if _setting(settings, "operations_queue_backend") == "redis":
        return ReadinessService(status="blocked", detail="Redis queue backend is selected but REDIS_URL is missing.")
    return ReadinessService(status="disabled", detail="Redis is not required for the current no-billing runtime.")


def _object_storage_status(settings: object) -> ReadinessService:
    """Report whether object storage is ready for production media."""

    backend = str(_setting(settings, "object_storage_backend") or "in_memory")
    if backend == "s3" and _configured(_setting(settings, "object_storage_bucket_name")):
        return ReadinessService(status="configured", detail="S3-compatible object storage bucket is configured.")
    if backend == "s3":
        return ReadinessService(status="blocked", detail="S3-compatible storage is selected but bucket is missing.")
    return ReadinessService(status="disabled", detail="Runtime uses in-memory object storage for no-billing checks.")


def _qdrant_status(settings: object) -> ReadinessService:
    """Report whether vector search is configured."""

    if _configured(_setting(settings, "qdrant_url")):
        return ReadinessService(status="configured", detail="Qdrant URL is configured.")
    return ReadinessService(status="disabled", detail="Qdrant is not configured for this runtime.")


def _auth_status(settings: object) -> ReadinessService:
    """Report whether admin/public auth is production-ready."""

    if _configured(_setting(settings, "admin_api_token")):
        return ReadinessService(status="configured", detail="Admin API bearer token is configured.")
    if bool(_setting(settings, "allow_unsafe_admin_header_auth")):
        return ReadinessService(status="blocked", detail="Unsafe admin header auth is enabled and must not ship.")
    return ReadinessService(status="blocked", detail="Production admin/public auth provider is not configured.")


def _billing_status(settings: object) -> ReadinessService:
    """Report whether backend-owned billing and credit ledger can run."""

    if bool(_setting(settings, "billing_core_enabled")):
        return ReadinessService(status="configured", detail="Billing core is enabled for backend credit ledger flows.")
    return ReadinessService(status="blocked", detail="Billing core is disabled; paid flows must stay gated.")


def _ai_provider_status(settings: object) -> ReadinessService:
    """Report whether reasoning provider settings are production-ready."""

    provider = str(_setting(settings, "llm_provider") or "fake")
    mode = str(_setting(settings, "llm_gateway_mode") or "stub")
    if provider == "fake" or mode == "stub":
        return ReadinessService(status="blocked", detail="Reasoning provider is still in fake/stub mode.")
    if provider in {"vertex", "gemini_structured"} and not _configured(_setting(settings, "vertex_project")):
        return ReadinessService(status="blocked", detail="Vertex/Gemini provider is selected but project is missing.")
    return ReadinessService(status="configured", detail=f"Reasoning provider is configured as {provider}.")


def _image_editing_status(settings: object) -> ReadinessService:
    """Report whether image editing/generation is production-ready."""

    provider = str(_setting(settings, "image_editing_provider") or "stub")
    real_try_on_enabled = bool(_setting(settings, "enable_real_try_on_generation"))
    if provider == "stub" and real_try_on_enabled:
        return ReadinessService(status="blocked", detail="Real try-on is enabled but image editing provider is stub.")
    if provider == "stub":
        return ReadinessService(status="disabled", detail="Image editing provider is stubbed for no-billing checks.")
    return ReadinessService(status="configured", detail=f"Image editing provider is configured as {provider}.")


def _search_engine_discovery_status(settings: object) -> ReadinessService:
    """Report whether open-web/Instagram discovery can use approved search sources."""

    enabled = bool(_setting(settings, "enable_search_engine_discovery"))
    provider = str(_setting(settings, "search_engine_discovery_provider") or "disabled")
    has_key = _configured(_setting(settings, "search_engine_discovery_api_key"))
    daily_limit = int(_setting(settings, "search_engine_discovery_daily_limit") or 0)
    if not enabled:
        return ReadinessService(status="disabled", detail="Search-engine discovery is disabled.")
    if provider == "disabled" or not has_key or daily_limit <= 0:
        return ReadinessService(status="blocked", detail="Discovery is enabled but provider, API key, or daily limit is missing.")
    return ReadinessService(status="configured", detail=f"Search-engine discovery is configured through {provider}.")


def _admin_surface_status(settings: object) -> ReadinessService:
    """Report whether admin review surfaces are switched on for backend contracts."""

    enabled = any(
        bool(_setting(settings, name))
        for name in ("enable_admin_business_catalog", "enable_admin_taxonomy", "enable_admin_costs")
    )
    if enabled:
        return ReadinessService(status="configured", detail="Admin backend feature flags are enabled.")
    return ReadinessService(status="disabled", detail="Admin backend feature flags are disabled.")


def _setting(settings: object, name: str) -> object | None:
    """Read one setting without assuming a concrete settings class."""

    return getattr(settings, name, None)


def _configured(value: object | None) -> bool:
    """Return True when a string-like config value is present and not a placeholder."""

    if value is None:
        return False
    normalized = str(value).strip()
    if not normalized:
        return False
    return not normalized.upper().startswith("TBD_")
