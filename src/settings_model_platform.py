"""Portable platform foundation settings fields."""
from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator


class PlatformSettingsMixin(BaseModel):
    """Storage, queue, vector, and billing settings."""

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
    object_storage_region: str | None = Field(default=None, validation_alias=AliasChoices("OBJECT_STORAGE_REGION"))
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
    billing_core_enabled: bool = Field(default=False, validation_alias=AliasChoices("BILLING_CORE_ENABLED"))
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
    processing_lease_duration_seconds: int = 300
    processing_lease_renew_interval_seconds: int = 60
    processing_stale_reclaim_seconds: int = 300

    @model_validator(mode="after")
    def _validate_portable_foundation_settings(self):
        object_storage_bucket_name = (self.object_storage_bucket_name or "").strip()
        redis_url = (self.redis_url or "").strip()
        qdrant_url = (self.qdrant_url or "").strip()
        vertex_project = (getattr(self, "vertex_project", None) or "").strip()
        if self.object_storage_backend == "s3" and not object_storage_bucket_name:
            raise ValueError("object_storage_bucket_name is required when object_storage_backend is s3")
        if getattr(self, "try_on_generation_backend", None) == "vertex_virtual_try_on" and not vertex_project:
            raise ValueError("vertex_project is required when try_on_generation_backend is vertex_virtual_try_on")
        if self.redis_url is not None and not redis_url:
            raise ValueError("redis_url must not be blank when provided")
        if self.qdrant_url is not None and not qdrant_url:
            raise ValueError("qdrant_url must not be blank when provided")
        return self
