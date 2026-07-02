"""Try-on specific settings fields and validators."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator
from pydantic_settings import NoDecode


class TryOnSettingsMixin(BaseModel):
    """Try-on workflow settings."""

    try_on_allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp"],
        validation_alias=AliasChoices("TRY_ON_ALLOWED_CONTENT_TYPES"),
    )
    try_on_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
        validation_alias=AliasChoices("TRY_ON_MAX_UPLOAD_BYTES"),
    )
    try_on_human_identity_timeout_seconds: float = Field(
        default=60.0,
        gt=0.0,
        le=300.0,
        validation_alias=AliasChoices("TRY_ON_HUMAN_IDENTITY_TIMEOUT_SECONDS"),
    )
    try_on_human_identity_minimum_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("TRY_ON_HUMAN_IDENTITY_MINIMUM_CONFIDENCE"),
    )
    try_on_human_identity_preferred_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TRY_ON_HUMAN_IDENTITY_PREFERRED_MODEL"),
    )
    try_on_garment_identity_timeout_seconds: float = Field(
        default=90.0,
        gt=0.0,
        le=300.0,
        validation_alias=AliasChoices("TRY_ON_GARMENT_IDENTITY_TIMEOUT_SECONDS"),
    )
    try_on_garment_identity_minimum_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("TRY_ON_GARMENT_IDENTITY_MINIMUM_CONFIDENCE"),
    )
    try_on_garment_identity_preferred_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TRY_ON_GARMENT_IDENTITY_PREFERRED_MODEL"),
    )
    try_on_material_texture_timeout_seconds: float = Field(
        default=90.0,
        gt=0.0,
        le=300.0,
        validation_alias=AliasChoices("TRY_ON_MATERIAL_TEXTURE_TIMEOUT_SECONDS"),
    )
    try_on_material_texture_minimum_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("TRY_ON_MATERIAL_TEXTURE_MINIMUM_CONFIDENCE"),
    )
    try_on_material_texture_preferred_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TRY_ON_MATERIAL_TEXTURE_PREFERRED_MODEL"),
    )
    try_on_instruction_timeout_seconds: float = Field(
        default=60.0,
        gt=0.0,
        le=300.0,
        validation_alias=AliasChoices("TRY_ON_INSTRUCTION_TIMEOUT_SECONDS"),
    )
    try_on_instruction_minimum_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("TRY_ON_INSTRUCTION_MINIMUM_CONFIDENCE"),
    )
    try_on_instruction_preferred_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TRY_ON_INSTRUCTION_PREFERRED_MODEL"),
    )
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
        default="deterministic",
        validation_alias=AliasChoices("TRY_ON_QUALITY_VERIFIER_BACKEND"),
    )
    try_on_repair_backend: Literal["deterministic", "provider_runtime"] = Field(
        default="deterministic",
        validation_alias=AliasChoices("TRY_ON_REPAIR_BACKEND"),
    )
    try_on_stylist_backend: Literal["deterministic", "model_backed"] = Field(
        default="deterministic",
        validation_alias=AliasChoices("TRY_ON_STYLIST_BACKEND"),
    )
    allow_unsafe_try_on_vertex_fallback_in_production: bool = Field(
        default=False,
        validation_alias=AliasChoices("ALLOW_UNSAFE_TRY_ON_VERTEX_FALLBACK_IN_PRODUCTION"),
    )

    @field_validator("try_on_allowed_content_types", mode="before")
    @classmethod
    def _parse_try_on_content_types(cls, value: object) -> list[str]:
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
    def _validate_try_on_activation_settings(self):
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
        if getattr(self, "object_storage_backend", None) != "s3":
            raise ValueError("object_storage_backend must be s3 when enable_real_try_on_generation is true")
        if not (getattr(self, "postgres_dsn", None) or "").strip():
            raise ValueError("postgres_dsn is required when enable_real_try_on_generation is true")
        if getattr(self, "operations_queue_backend", None) != "redis":
            raise ValueError("operations_queue_backend must be redis when enable_real_try_on_generation is true")
        if not (getattr(self, "redis_url", None) or "").strip():
            raise ValueError("redis_url is required when enable_real_try_on_generation is true")
        if not (getattr(self, "vertex_project", None) or "").strip():
            raise ValueError("vertex_project is required when enable_real_try_on_generation is true")
        return self
