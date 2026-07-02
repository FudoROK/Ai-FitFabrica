"""Runtime helpers for settings loading and fail-fast validation."""
from __future__ import annotations

import logging
import os
from functools import lru_cache

from .settings_contracts import CRMSettings, LLMSettings
from .utils.log_redaction import RedactingLogFilter, install_redaction_logging_policy
from .utils.structured_logging import configure_structured_logging

logger = logging.getLogger(__name__)


def should_skip_dotenv() -> bool:
    """Skip .env loading for pytest/test environment isolation."""

    environment = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or os.getenv("ENV") or "").strip().lower()
    return environment == "test" or "PYTEST_CURRENT_TEST" in os.environ


def is_dev_mode(settings) -> bool:
    """Return True when debug-level dependency logs are acceptable."""

    env = (settings.environment or "").strip().lower()
    if env in {"dev", "local", "development"}:
        return True
    debug_flag = (os.getenv("DEBUG") or "").strip().lower()
    return debug_flag in {"1", "true", "yes", "on"}


def is_production_like_environment(environment: str) -> bool:
    normalized = (environment or "").strip().lower()
    return normalized in {"prod", "production", "staging", "stage", "preprod", "preproduction"}


def configure_dependency_log_levels(settings) -> None:
    """Prevent sensitive data leakage from verbose third-party loggers."""

    dependency_level_name = settings.log_level.upper() if is_dev_mode(settings) else "WARNING"
    dependency_level = getattr(logging, dependency_level_name, logging.WARNING)
    logging.getLogger("httpx").setLevel(dependency_level)
    logging.getLogger("httpcore").setLevel(dependency_level)


def ensure_redaction_logging_enforced() -> None:
    """Ensure redaction policy stays attached to the active root logging pipeline."""

    install_redaction_logging_policy()
    root_logger = logging.getLogger()
    if not any(isinstance(flt, RedactingLogFilter) for flt in root_logger.filters):
        root_logger.addFilter(RedactingLogFilter())
    for handler in root_logger.handlers:
        if not any(isinstance(flt, RedactingLogFilter) for flt in handler.filters):
            handler.addFilter(RedactingLogFilter())


def build_llm_settings(settings) -> LLMSettings:
    return LLMSettings(
        provider=settings.llm_provider,
        mode=settings.llm_gateway_mode,
        model=settings.llm_model,
        vertex_project=settings.vertex_project,
        vertex_location=settings.vertex_location,
        vertex_agent_resource=settings.vertex_agent_resource,
    )


def build_crm_settings(settings) -> CRMSettings:
    return CRMSettings(
        crm_access_token=settings.crm_access_token,
        crm_base_url=settings.crm_base_url,
        sync_enabled=settings.crm_sync_enabled and settings.crm_hubspot_sync_enabled,
    )


def validate_settings(settings) -> None:
    """Fail-fast checks for conditional mandatory settings."""

    missing: list[str] = []
    if settings.llm.provider in {"vertex", "gemini_structured"} and not settings.llm.vertex_project:
        missing.append("VERTEX_PROJECT (required when LLM_PROVIDER is vertex or gemini_structured)")
    if settings.try_on_generation_backend == "vertex_virtual_try_on" and not settings.vertex_project:
        missing.append("VERTEX_PROJECT (required when TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on)")
    if settings.try_on_generation_backend == "vertex_virtual_try_on" and not settings.enable_real_try_on_generation:
        missing.append("ENABLE_REAL_TRY_ON_GENERATION=true (required when TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on)")
    if settings.enable_real_try_on_generation:
        if settings.object_storage_backend != "s3":
            missing.append("OBJECT_STORAGE_BACKEND=s3 (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
        if not (settings.postgres_dsn or "").strip():
            missing.append("POSTGRES_DSN (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
        if settings.operations_queue_backend != "redis":
            missing.append("OPERATIONS_QUEUE_BACKEND=redis (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
        if not (settings.redis_url or "").strip():
            missing.append("REDIS_URL (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
    if settings.crm_provider == "hubspot" and settings.crm_sync_enabled and not settings.crm.crm_access_token:
        missing.append("CRM_ACCESS_TOKEN (required when CRM_PROVIDER=hubspot and crm_sync_enabled=true)")
    if settings.processing_lease_renew_interval_seconds >= settings.processing_lease_duration_seconds:
        missing.append("PROCESSING_LEASE_RENEW_INTERVAL_SECONDS must be lower than PROCESSING_LEASE_DURATION_SECONDS")
    if settings.processing_stale_reclaim_seconds < settings.processing_lease_duration_seconds:
        missing.append("PROCESSING_STALE_RECLAIM_SECONDS must be >= PROCESSING_LEASE_DURATION_SECONDS")
    if (
        is_production_like_environment(settings.environment)
        and settings.rate_limit_fail_mode == "open"
        and not settings.allow_unsafe_rate_limit_fail_open_in_production
    ):
        missing.append(
            "RATE_LIMIT_FAIL_MODE=open is not allowed in production-like environments. "
            "Set RATE_LIMIT_FAIL_MODE=closed or explicitly set "
            "ALLOW_UNSAFE_RATE_LIMIT_FAIL_OPEN_IN_PRODUCTION=true to bypass this startup guard."
        )
    if (
        is_production_like_environment(settings.environment)
        and settings.enable_real_try_on_generation
        and settings.try_on_vertex_failure_fallback_backend != "none"
        and not settings.allow_unsafe_try_on_vertex_fallback_in_production
    ):
        missing.append(
            "TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND is not allowed in production-like environments when "
            "ENABLE_REAL_TRY_ON_GENERATION=true. Set TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND=none or explicitly set "
            "ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION=true to bypass this startup guard."
        )
    if missing:
        raise ValueError(f"Invalid settings: missing required environment variables: {'; '.join(missing)}")


def bind_settings_loader(Settings):
    """Create cached load functions for the provided Settings class."""

    @lru_cache()
    def _load_settings_cached():
        settings = Settings(_env_file=None) if should_skip_dotenv() else Settings()
        validate_settings(settings)
        return settings

    def load_settings():
        settings = _load_settings_cached()
        configure_structured_logging(level=getattr(logging, settings.log_level.upper(), logging.INFO))
        ensure_redaction_logging_enforced()
        configure_dependency_log_levels(settings)
        return settings

    load_settings.cache_clear = _load_settings_cached.cache_clear  # type: ignore[attr-defined]
    load_settings.cache_info = _load_settings_cached.cache_info  # type: ignore[attr-defined]
    return load_settings
