"""Centralized, validated application settings (single env source)."""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from dataclasses import dataclass
from typing import Annotated, Literal, Optional

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from .utils.log_redaction import RedactingLogFilter, install_redaction_logging_policy
from .utils.structured_logging import configure_structured_logging

logger = logging.getLogger(__name__)


def _should_skip_dotenv() -> bool:
    """Skip .env loading for pytest/test environment isolation."""
    environment = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or os.getenv("ENV") or "").strip().lower()
    return environment == "test" or "PYTEST_CURRENT_TEST" in os.environ


def _is_dev_mode(settings: "Settings") -> bool:
    """Return True when debug-level dependency logs are acceptable."""
    env = (settings.environment or "").strip().lower()
    if env in {"dev", "local", "development"}:
        return True

    debug_flag = (os.getenv("DEBUG") or "").strip().lower()
    return debug_flag in {"1", "true", "yes", "on"}


def _is_production_like_environment(environment: str) -> bool:
    normalized = (environment or "").strip().lower()
    return normalized in {"prod", "production", "staging", "stage", "preprod", "preproduction"}


def _configure_dependency_log_levels(settings: "Settings") -> None:
    """Prevent sensitive data leakage from verbose third-party loggers."""
    if _is_dev_mode(settings):
        dependency_level_name = settings.log_level.upper()
    else:
        dependency_level_name = "WARNING"

    dependency_level = getattr(logging, dependency_level_name, logging.WARNING)
    logging.getLogger("httpx").setLevel(dependency_level)
    logging.getLogger("httpcore").setLevel(dependency_level)


def _ensure_redaction_logging_enforced() -> None:
    """
    Ensure redaction policy is applied to the root pipeline and to any handlers
    that may have been attached after the first settings load.
    """
    install_redaction_logging_policy()

    root_logger = logging.getLogger()
    if not any(isinstance(flt, RedactingLogFilter) for flt in root_logger.filters):
        root_logger.addFilter(RedactingLogFilter())

    for handler in root_logger.handlers:
        if not any(isinstance(flt, RedactingLogFilter) for flt in handler.filters):
            handler.addFilter(RedactingLogFilter())


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    mode: str
    model: str
    vertex_project: Optional[str]
    vertex_location: Optional[str]
    vertex_agent_resource: Optional[str]
    vertex_memory_daily_agent_resource: Optional[str]
    vertex_memory_rolling_agent_resource: Optional[str]


@dataclass(frozen=True)
class CRMSettings:
    crm_access_token: Optional[str]
    crm_base_url: str
    sync_enabled: bool


class Settings(BaseSettings):
    """Strongly typed application configuration + compatibility aliases."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow")

    # App runtime
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    environment: str = Field("prod", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV", "ENV"))
    log_level: str = "INFO"
    bot_key: str = "fitfabrica_backend"
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS"),
    )
    cors_allowed_origin_regex: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGIN_REGEX"),
    )

    # Integration providers
    crm_provider: str = Field("none", validation_alias=AliasChoices("CRM_PROVIDER"))
    calendar_provider: str = Field("none", validation_alias=AliasChoices("CALENDAR_PROVIDER"))
    messaging_provider: str = Field("none", validation_alias=AliasChoices("MESSAGING_PROVIDER"))

    # Pub/Sub + GCP
    gcp_project_id: str = Field(
        ...,
        validation_alias=AliasChoices("PROJECT_ID", "RUNTIME_PROJECT_ID", "GCP_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    maps_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("MAPS_API_KEY"),
    )
    pubsub_topic_name: str = Field(
        ...,
        validation_alias=AliasChoices("EVENT_TOPIC_NAME", "PUBSUB_TOPIC_NAME", "PUBSUB_TOPIC_ID"),
    )
    pubsub_topic_id: Optional[str] = None

    # Admin/memory jobs
    admin_chat_ids: list[int] = Field(default_factory=list)
    memory_summary_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("MEMORY_SUMMARY_ENABLED"),
    )
    enable_profile_runtime: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_PROFILE_RUNTIME"),
    )
    enable_memory_profile: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_MEMORY_PROFILE"),
    )
    allow_unsafe_memory_process_use_case_override: bool = Field(
        default=False,
        validation_alias=AliasChoices("ALLOW_UNSAFE_MEMORY_PROCESS_USE_CASE_OVERRIDE"),
    )
    memory_summary_timezone: str = "Asia/Almaty"
    memory_summary_batch_limit: int = 100
    memory_summary_task_auth_audience: Optional[str] = None
    memory_summary_task_allowed_service_accounts: Annotated[list[str], NoDecode] = Field(default_factory=list)
    memory_rolling_pointer_read_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("MEMORY_ROLLING_POINTER_READ_ENABLED"),
    )
    public_status_endpoints_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("PUBLIC_STATUS_ENDPOINTS_ENABLED"),
    )
    status_endpoint_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STATUS_ENDPOINT_TOKEN"),
    )
    try_on_allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp"],
        validation_alias=AliasChoices("TRY_ON_ALLOWED_CONTENT_TYPES"),
    )
    try_on_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
        validation_alias=AliasChoices("TRY_ON_MAX_UPLOAD_BYTES"),
    )
    try_on_job_repository_backend: Literal["in_memory", "firestore"] = "in_memory"
    try_on_firestore_collection: str = "try_on_jobs"
    try_on_generation_backend: Literal["sandbox_fake", "provider_runtime", "vertex_virtual_try_on"] = Field(
        default="sandbox_fake",
        validation_alias=AliasChoices("TRY_ON_GENERATION_BACKEND"),
    )
    enable_real_try_on_generation: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_REAL_TRY_ON_GENERATION"),
    )
    try_on_vertex_failure_fallback_backend: Literal["none", "provider_runtime", "sandbox_fake"] = Field(
        default="none",
        validation_alias=AliasChoices("TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND"),
    )
    try_on_quality_verifier_backend: Literal["deterministic", "model_backed"] = Field(
        default="model_backed",
        validation_alias=AliasChoices("TRY_ON_QUALITY_VERIFIER_BACKEND"),
    )
    try_on_repair_backend: Literal["deterministic", "provider_runtime"] = Field(
        default="provider_runtime",
        validation_alias=AliasChoices("TRY_ON_REPAIR_BACKEND"),
    )
    try_on_stylist_backend: Literal["deterministic", "model_backed"] = Field(
        default="model_backed",
        validation_alias=AliasChoices("TRY_ON_STYLIST_BACKEND"),
    )

    # LLM
    llm_provider: str = Field("vertex", validation_alias=AliasChoices("LLM_PROVIDER"))
    llm_gateway_mode: str = Field("stub", validation_alias=AliasChoices("LLM_GATEWAY_MODE", "LLM_MODE"))
    llm_model: str = Field("gemini-2.0-flash", validation_alias=AliasChoices("LLM_MODEL", "VERTEX_MODEL"))

    # Vertex runtime
    vertex_project: Optional[str] = Field(default=None, validation_alias=AliasChoices("VERTEX_PROJECT"))
    vertex_location: Optional[str] = Field(default="us-central1", validation_alias=AliasChoices("VERTEX_LOCATION"))
    vertex_virtual_try_on_location: Optional[str] = Field(
        default="global",
        validation_alias=AliasChoices("VERTEX_VIRTUAL_TRY_ON_LOCATION"),
    )
    vertex_virtual_try_on_model: str = Field(
        default="virtual-try-on-001",
        validation_alias=AliasChoices("VERTEX_VIRTUAL_TRY_ON_MODEL"),
    )
    vertex_agent_resource: Optional[str] = Field(default=None, validation_alias=AliasChoices("VERTEX_AGENT_RESOURCE"))
    vertex_memory_daily_agent_resource: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("VERTEX_MEMORY_DAILY_AGENT_RESOURCE"),
    )
    vertex_memory_rolling_agent_resource: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("VERTEX_MEMORY_ROLLING_AGENT_RESOURCE"),
    )

    # Runtime rate limiting
    enable_distributed_rate_limit: bool = True
    rate_limit_backend: str = Field(default="redis", validation_alias=AliasChoices("RATE_LIMIT_BACKEND"))
    rate_limit_max_events: int = 10
    rate_limit_window_seconds: int = 60
    rate_limit_fail_mode: str = "closed"
    allow_unsafe_rate_limit_fail_open_in_production: bool = False
    rate_limit_collection: str = "runtime_rate_limits"
    ingress_rate_limit_max_events: int = 20
    ingress_rate_limit_window_seconds: int = 60
    ingress_rate_limit_collection: str = "ingress_rate_limits"
    ingress_global_safety_cap_max_events: int = 2000

    # Portable platform foundation
    postgres_dsn: str | None = Field(default=None, validation_alias=AliasChoices("POSTGRES_DSN", "DATABASE_URL"))
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20
    postgres_pool_timeout_seconds: int = 30
    redis_url: str | None = Field(default=None, validation_alias=AliasChoices("REDIS_URL"))
    redis_key_prefix: str = "fitfabrica"
    object_storage_backend: Literal["in_memory", "s3"] = Field(
        default="in_memory",
        validation_alias=AliasChoices("OBJECT_STORAGE_BACKEND"),
    )
    object_storage_bucket_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OBJECT_STORAGE_BUCKET_NAME"),
    )
    object_storage_region: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OBJECT_STORAGE_REGION"),
    )
    object_storage_endpoint_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OBJECT_STORAGE_ENDPOINT_URL"),
    )
    object_storage_access_key_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OBJECT_STORAGE_ACCESS_KEY_ID"),
    )
    object_storage_secret_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OBJECT_STORAGE_SECRET_ACCESS_KEY"),
    )
    object_storage_prefix: str = "fitfabrica"
    object_storage_signed_url_ttl_seconds: int = Field(
        default=900,
        ge=60,
        le=86400,
        validation_alias=AliasChoices("OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS"),
    )
    object_storage_tenant_prefix_mode: Literal["shared", "tenant_scoped"] = Field(
        default="shared",
        validation_alias=AliasChoices("OBJECT_STORAGE_TENANT_PREFIX_MODE"),
    )
    vector_backend: Literal["qdrant"] = Field(default="qdrant", validation_alias=AliasChoices("VECTOR_BACKEND"))
    qdrant_url: str | None = Field(default=None, validation_alias=AliasChoices("QDRANT_URL"))
    qdrant_api_key: str | None = Field(default=None, validation_alias=AliasChoices("QDRANT_API_KEY"))
    qdrant_collection_prefix: str = "fitfabrica"
    qdrant_request_timeout_seconds: float = 10.0
    billing_core_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("BILLING_CORE_ENABLED"),
    )
    default_person_credit_account_id: str = Field(
        default="public-person",
        validation_alias=AliasChoices("DEFAULT_PERSON_CREDIT_ACCOUNT_ID"),
    )
    default_business_credit_account_id: str = Field(
        default="public-business",
        validation_alias=AliasChoices("DEFAULT_BUSINESS_CREDIT_ACCOUNT_ID"),
    )
    try_on_base_credit_cost: int = Field(default=12, ge=0, validation_alias=AliasChoices("TRY_ON_BASE_CREDIT_COST"))
    product_card_base_credit_cost: int = Field(
        default=18,
        ge=0,
        validation_alias=AliasChoices("PRODUCT_CARD_BASE_CREDIT_COST"),
    )
    content_package_base_credit_cost: int = Field(
        default=14,
        ge=0,
        validation_alias=AliasChoices("CONTENT_PACKAGE_BASE_CREDIT_COST"),
    )
    pricing_base_credit_cost: int = Field(default=6, ge=0, validation_alias=AliasChoices("PRICING_BASE_CREDIT_COST"))
    operations_queue_backend: Literal["in_memory", "redis"] = Field(
        default="in_memory",
        validation_alias=AliasChoices("OPERATIONS_QUEUE_BACKEND"),
    )
    operations_queue_name: str = Field(
        default="fitfabrica:workflow-queue",
        validation_alias=AliasChoices("OPERATIONS_QUEUE_NAME"),
    )
    operations_worker_name: str = Field(
        default="portable-worker",
        validation_alias=AliasChoices("OPERATIONS_WORKER_NAME"),
    )
    operations_worker_poll_interval_seconds: float = Field(
        default=1.0,
        gt=0,
        validation_alias=AliasChoices("OPERATIONS_WORKER_POLL_INTERVAL_SECONDS"),
    )
    allow_unsafe_try_on_vertex_fallback_in_production: bool = Field(
        default=False,
        validation_alias=AliasChoices("ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION"),
    )

    # Processing lease / reclaim safety
    processing_lease_duration_seconds: int = 300
    processing_lease_renew_interval_seconds: int = 60
    processing_stale_reclaim_seconds: int = 300

    # CRM runtime flags
    crm_sync_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("CRM_SYNC_ENABLED", "HUBSPOT_SYNC_ENABLED"),
    )
    crm_memory_sync_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("CRM_MEMORY_SYNC_ENABLED"),
    )
    crm_profile_sync_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("CRM_PROFILE_SYNC_ENABLED"),
    )

    # HubSpot (provider-specific section + legacy aliases)
    crm_access_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CRM_ACCESS_TOKEN", "HUBSPOT_ACCESS_TOKEN", "HUBSPOT_PRIVATE_APP_TOKEN"),
    )
    crm_base_url: str = "https://api.hubapi.com"
    crm_hubspot_sync_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("HUBSPOT_SYNC_ENABLED", "CRM_SYNC_ENABLED"),
    )

    @field_validator("gcp_project_id")
    @classmethod
    def _project_required(cls, value: str) -> str:
        if not value:
            raise ValueError("project id must be provided")
        return value

    @field_validator("admin_chat_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value):
        if value in (None, "", []):
            return []
        if isinstance(value, (list, tuple)):
            return [int(item) for item in value]
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return [int(part) for part in parts]
        return [int(value)]

    @field_validator("pubsub_topic_id")
    @classmethod
    def _default_topic_id(cls, value, info):
        if value:
            return value
        return info.data.get("pubsub_topic_name")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_allowed_origins(cls, value: object) -> list[str]:
        """Parse comma-separated frontend origins allowed to call the API from browsers."""
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [part.strip().rstrip("/") for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip().rstrip("/") for item in value if str(item).strip()]
        return [str(value).strip().rstrip("/")] if str(value).strip() else []

    @field_validator("cors_allowed_origin_regex", mode="before")
    @classmethod
    def _parse_cors_allowed_origin_regex(cls, value: object) -> str | None:
        """Normalize the optional browser-origin regex for dynamic frontend hosts."""
        if value in (None, "", []):
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator(
        "memory_summary_task_allowed_service_accounts",
        mode="before",
    )
    @classmethod
    def _parse_service_account_allowlist(cls, value):
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [part.strip().lower() for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip().lower() for item in value if str(item).strip()]
        return [str(value).strip().lower()]

    @field_validator("try_on_allowed_content_types", mode="before")
    @classmethod
    def _parse_try_on_content_types(cls, value: object) -> list[str]:
        """Parse comma-separated Try-On upload MIME types with default fallback for blank input."""
        if value in (None, "", []):
            return ["image/jpeg", "image/png", "image/webp"]
        if isinstance(value, str):
            parsed = [part.strip().lower() for part in value.split(",") if part.strip()]
            return parsed or ["image/jpeg", "image/png", "image/webp"]
        if isinstance(value, (list, tuple, set)):
            parsed = [str(item).strip().lower() for item in value if str(item).strip()]
            return parsed or ["image/jpeg", "image/png", "image/webp"]
        parsed = [str(value).strip().lower()] if str(value).strip() else []
        return parsed or ["image/jpeg", "image/png", "image/webp"]

    @model_validator(mode="after")
    def _validate_try_on_storage_settings(self) -> "Settings":
        """Validate Try-On repository settings before app startup."""
        firestore_collection = self.try_on_firestore_collection.strip()

        if self.try_on_job_repository_backend == "firestore" and not firestore_collection:
            raise ValueError(
                "try_on_firestore_collection is required when try_on_job_repository_backend is firestore"
            )
        return self

    @model_validator(mode="after")
    def _validate_portable_foundation_settings(self) -> "Settings":
        """Validate portable infrastructure config without forcing local bootstrap credentials."""
        object_storage_bucket_name = (self.object_storage_bucket_name or "").strip()
        redis_url = (self.redis_url or "").strip()
        qdrant_url = (self.qdrant_url or "").strip()
        vertex_project = (self.vertex_project or "").strip()

        if self.object_storage_backend == "s3" and not object_storage_bucket_name:
            raise ValueError("object_storage_bucket_name is required when object_storage_backend is s3")
        if self.try_on_generation_backend == "vertex_virtual_try_on" and not vertex_project:
            raise ValueError("vertex_project is required when try_on_generation_backend is vertex_virtual_try_on")
        if self.redis_url is not None and not redis_url:
            raise ValueError("redis_url must not be blank when provided")
        if self.qdrant_url is not None and not qdrant_url:
            raise ValueError("qdrant_url must not be blank when provided")
        return self

    @model_validator(mode="after")
    def _validate_try_on_activation_settings(self) -> "Settings":
        """Guard the real Vertex Try-On rollout behind explicit activation settings."""
        if self.try_on_generation_backend == "vertex_virtual_try_on" and not self.enable_real_try_on_generation:
            raise ValueError(
                "enable_real_try_on_generation must be true when try_on_generation_backend is vertex_virtual_try_on"
            )
        if self.enable_real_try_on_generation and self.try_on_generation_backend != "vertex_virtual_try_on":
            raise ValueError(
                "try_on_generation_backend must be vertex_virtual_try_on when enable_real_try_on_generation is true"
            )
        if not self.enable_real_try_on_generation:
            return self

        postgres_dsn = (self.postgres_dsn or "").strip()
        redis_url = (self.redis_url or "").strip()
        vertex_project = (self.vertex_project or "").strip()

        if self.object_storage_backend != "s3":
            raise ValueError("object_storage_backend must be s3 when enable_real_try_on_generation is true")
        if not postgres_dsn:
            raise ValueError("postgres_dsn is required when enable_real_try_on_generation is true")
        if self.operations_queue_backend != "redis":
            raise ValueError("operations_queue_backend must be redis when enable_real_try_on_generation is true")
        if not redis_url:
            raise ValueError("redis_url is required when enable_real_try_on_generation is true")
        if not vertex_project:
            raise ValueError("vertex_project is required when enable_real_try_on_generation is true")
        return self

    @field_validator("crm_provider")
    @classmethod
    def _normalize_crm_provider(cls, value: str) -> str:
        normalized = (value or "none").strip().lower()
        if normalized not in {"hubspot", "none"}:
            raise ValueError("CRM_PROVIDER must be one of: hubspot, none")
        return normalized

    @field_validator("calendar_provider")
    @classmethod
    def _normalize_calendar_provider(cls, value: str) -> str:
        normalized = (value or "none").strip().lower()
        if normalized not in {"none"}:
            raise ValueError("CALENDAR_PROVIDER must be one of: none")
        return normalized

    @field_validator("messaging_provider")
    @classmethod
    def _normalize_messaging_provider(cls, value: str) -> str:
        normalized = (value or "none").strip().lower()
        if normalized != "none":
            raise ValueError("MESSAGING_PROVIDER must be one of: none")
        return normalized

    @field_validator("rate_limit_backend")
    @classmethod
    def _normalize_rate_limit_backend(cls, value: str) -> str:
        normalized = (value or "redis").strip().lower()
        if normalized not in {"redis", "inmemory"}:
            raise ValueError("RATE_LIMIT_BACKEND must be one of: redis, inmemory")
        return normalized

    @field_validator("rate_limit_fail_mode")
    @classmethod
    def _normalize_rate_limit_fail_mode(cls, value: str) -> str:
        normalized = (value or "closed").strip().lower()
        if normalized not in {"open", "closed"}:
            raise ValueError("RATE_LIMIT_FAIL_MODE must be one of: open, closed")
        return normalized

    @field_validator("llm_provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in {"fake", "vertex", "gemini_structured"}:
            raise ValueError("LLM_PROVIDER must be one of: fake, vertex, gemini_structured")
        return normalized

    @field_validator("llm_gateway_mode")
    @classmethod
    def _normalize_mode(cls, value: str) -> str:
        return (value or "stub").strip().lower()

    @field_validator(
        "processing_lease_duration_seconds",
        "processing_lease_renew_interval_seconds",
        "processing_stale_reclaim_seconds",
    )
    @classmethod
    def _validate_positive_processing_timers(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("Processing lease intervals must be positive integers")
        return int(value)

    @field_validator(
        "rate_limit_max_events",
        "rate_limit_window_seconds",
        "ingress_rate_limit_max_events",
        "ingress_rate_limit_window_seconds",
        "ingress_global_safety_cap_max_events",
    )
    @classmethod
    def _validate_positive_rate_limits(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("Rate limit values must be positive integers")
        return int(value)

    @property
    def llm(self) -> LLMSettings:
        return LLMSettings(
            provider=self.llm_provider,
            mode=self.llm_gateway_mode,
            model=self.llm_model,
            vertex_project=self.vertex_project,
            vertex_location=self.vertex_location,
            vertex_agent_resource=self.vertex_agent_resource,
            vertex_memory_daily_agent_resource=self.vertex_memory_daily_agent_resource,
            vertex_memory_rolling_agent_resource=self.vertex_memory_rolling_agent_resource,
        )

    @property
    def crm(self) -> CRMSettings:
        return CRMSettings(
            crm_access_token=self.crm_access_token,
            crm_base_url=self.crm_base_url,
            sync_enabled=self.crm_sync_enabled and self.crm_hubspot_sync_enabled,
        )


def validate_settings(settings: Settings) -> None:
    """Fail-fast checks for conditional mandatory settings."""
    missing: list[str] = []

    if settings.llm.provider in {"vertex", "gemini_structured"}:
        if not settings.llm.vertex_project:
            missing.append("VERTEX_PROJECT (required when LLM_PROVIDER is vertex or gemini_structured)")

    if settings.try_on_generation_backend == "vertex_virtual_try_on" and not settings.vertex_project:
        missing.append("VERTEX_PROJECT (required when TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on)")

    if settings.try_on_generation_backend == "vertex_virtual_try_on" and not settings.enable_real_try_on_generation:
        missing.append(
            "ENABLE_REAL_TRY_ON_GENERATION=true (required when TRY_ON_GENERATION_BACKEND=vertex_virtual_try_on)"
        )

    if settings.enable_real_try_on_generation:
        if settings.object_storage_backend != "s3":
            missing.append("OBJECT_STORAGE_BACKEND=s3 (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
        if not (settings.postgres_dsn or "").strip():
            missing.append("POSTGRES_DSN (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
        if settings.operations_queue_backend != "redis":
            missing.append("OPERATIONS_QUEUE_BACKEND=redis (required when ENABLE_REAL_TRY_ON_GENERATION=true)")
        if not (settings.redis_url or "").strip():
            missing.append("REDIS_URL (required when ENABLE_REAL_TRY_ON_GENERATION=true)")

    if settings.llm.provider == "vertex" and not settings.llm.vertex_agent_resource:
        missing.append("VERTEX_AGENT_RESOURCE (required when LLM_PROVIDER=vertex)")

    if (
        settings.memory_summary_enabled
        and settings.llm.provider != "fake"
        and not (settings.llm.vertex_memory_daily_agent_resource and settings.llm.vertex_memory_rolling_agent_resource)
    ):
        missing.append(
            "VERTEX_MEMORY_DAILY_AGENT_RESOURCE and VERTEX_MEMORY_ROLLING_AGENT_RESOURCE "
            "(required for split memory runtime when memory summary is enabled)"
        )

    if settings.crm_provider == "hubspot" and settings.crm_sync_enabled and not settings.crm.crm_access_token:
        missing.append("CRM_ACCESS_TOKEN (required when CRM_PROVIDER=hubspot and crm_sync_enabled=true)")

    if settings.memory_summary_enabled:
        if not settings.memory_summary_task_auth_audience:
            missing.append("MEMORY_SUMMARY_TASK_AUTH_AUDIENCE (required for /tasks/memory-summary OIDC auth)")
        if not settings.memory_summary_task_allowed_service_accounts:
            missing.append(
                "MEMORY_SUMMARY_TASK_ALLOWED_SERVICE_ACCOUNTS (required for /tasks/memory-summary OIDC auth)"
            )

    if settings.processing_lease_renew_interval_seconds >= settings.processing_lease_duration_seconds:
        missing.append("PROCESSING_LEASE_RENEW_INTERVAL_SECONDS must be lower than PROCESSING_LEASE_DURATION_SECONDS")
    if settings.processing_stale_reclaim_seconds < settings.processing_lease_duration_seconds:
        missing.append("PROCESSING_STALE_RECLAIM_SECONDS must be >= PROCESSING_LEASE_DURATION_SECONDS")

    if (
        _is_production_like_environment(settings.environment)
        and settings.rate_limit_fail_mode == "open"
        and not settings.allow_unsafe_rate_limit_fail_open_in_production
    ):
        missing.append(
            "RATE_LIMIT_FAIL_MODE=open is not allowed in production-like environments. "
            "Set RATE_LIMIT_FAIL_MODE=closed or explicitly set "
            "ALLOW_UNSAFE_RATE_LIMIT_FAIL_OPEN_IN_PRODUCTION=true to bypass this startup guard."
        )

    if (
        _is_production_like_environment(settings.environment)
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
        formatted = "; ".join(missing)
        raise ValueError(f"Invalid settings: missing required environment variables: {formatted}")


@lru_cache()
def _load_settings_cached() -> Settings:
    """Load and validate settings once; safe to cache because this is pure config loading."""
    settings = Settings(_env_file=None) if _should_skip_dotenv() else Settings()
    validate_settings(settings)
    return settings


def load_settings() -> Settings:
    """
    Load settings and apply runtime logging side effects.

    Settings stay cached, while logging/bootstrap side effects are re-applied
    on every call so newly attached handlers also receive redaction filters.
    """
    settings = _load_settings_cached()
    configure_structured_logging(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    _ensure_redaction_logging_enforced()
    _configure_dependency_log_levels(settings)
    return settings


load_settings.cache_clear = _load_settings_cached.cache_clear  # type: ignore[attr-defined]
load_settings.cache_info = _load_settings_cached.cache_info  # type: ignore[attr-defined]
