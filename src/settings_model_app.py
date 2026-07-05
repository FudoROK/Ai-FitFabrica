"""Application and baseline runtime settings fields."""
from __future__ import annotations

from typing import Annotated, Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic_settings import NoDecode


class AppSettingsMixin(BaseModel):
    """Core application, HTTP, and memory baseline settings."""

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
    gcp_project_id: str = Field(
        ...,
        validation_alias=AliasChoices("PROJECT_ID", "RUNTIME_PROJECT_ID", "GCP_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    maps_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("MAPS_API_KEY"))
    pubsub_topic_name: str = Field(
        ...,
        validation_alias=AliasChoices("EVENT_TOPIC_NAME", "PUBSUB_TOPIC_NAME", "PUBSUB_TOPIC_ID"),
    )
    pubsub_topic_id: Optional[str] = None
    admin_chat_ids: list[int] = Field(default_factory=list)
    enable_profile_runtime: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_PROFILE_RUNTIME"))
    allow_unsafe_memory_process_use_case_override: bool = Field(
        default=False,
        validation_alias=AliasChoices("ALLOW_UNSAFE_MEMORY_PROCESS_USE_CASE_OVERRIDE"),
    )
    memory_rolling_pointer_read_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("MEMORY_ROLLING_POINTER_READ_ENABLED"),
    )
    public_status_endpoints_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("PUBLIC_STATUS_ENDPOINTS_ENABLED"),
    )
    enable_admin_taxonomy: bool = Field(default=False, validation_alias=AliasChoices("ENABLE_ADMIN_TAXONOMY"))
    enable_admin_business_catalog: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_ADMIN_BUSINESS_CATALOG"),
    )
    business_catalog_category_validation_mode: str = Field(
        default="agent",
        validation_alias=AliasChoices("BUSINESS_CATALOG_CATEGORY_VALIDATION_MODE"),
    )
    enable_admin_costs: bool = Field(default=False, validation_alias=AliasChoices("ENABLE_ADMIN_COSTS"))
    enable_search_engine_discovery: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_SEARCH_ENGINE_DISCOVERY"),
    )
    search_engine_discovery_provider: str = Field(
        default="disabled",
        validation_alias=AliasChoices("SEARCH_ENGINE_DISCOVERY_PROVIDER"),
    )
    search_engine_discovery_daily_limit: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("SEARCH_ENGINE_DISCOVERY_DAILY_LIMIT"),
    )
    search_engine_discovery_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("SEARCH_ENGINE_DISCOVERY_API_KEY"),
    )
    admin_api_token: Optional[str] = Field(default=None, validation_alias=AliasChoices("ADMIN_API_TOKEN"))
    allow_unsafe_admin_header_auth: bool = Field(
        default=False,
        validation_alias=AliasChoices("ALLOW_UNSAFE_ADMIN_HEADER_AUTH"),
    )
    status_endpoint_token: Optional[str] = Field(default=None, validation_alias=AliasChoices("STATUS_ENDPOINT_TOKEN"))
    auth_provider: str = Field(default="disabled", validation_alias=AliasChoices("AUTH_PROVIDER"))
    auth_session_cookie_name: str = Field(
        default="fitfabrica_session",
        validation_alias=AliasChoices("AUTH_SESSION_COOKIE_NAME"),
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
        if value in (None, "", []):
            return None
        normalized = str(value).strip()
        return normalized or None
