"""Provider selection and CRM-related settings fields."""
from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class ProviderSettingsMixin(BaseModel):
    """Provider routing and external service settings."""

    crm_provider: str = Field("none", validation_alias=AliasChoices("CRM_PROVIDER"))
    calendar_provider: str = Field("none", validation_alias=AliasChoices("CALENDAR_PROVIDER"))
    messaging_provider: str = Field("none", validation_alias=AliasChoices("MESSAGING_PROVIDER"))
    llm_provider: str = Field("vertex", validation_alias=AliasChoices("LLM_PROVIDER"))
    llm_gateway_mode: str = Field("stub", validation_alias=AliasChoices("LLM_GATEWAY_MODE", "LLM_MODE"))
    llm_model: str = Field("gemini-2.0-flash", validation_alias=AliasChoices("LLM_MODEL", "VERTEX_MODEL"))
    image_editing_provider: str = Field("stub", validation_alias=AliasChoices("IMAGE_EDITING_PROVIDER"))
    image_editing_model: Optional[str] = Field(default=None, validation_alias=AliasChoices("IMAGE_EDITING_MODEL"))
    image_editing_root_prefix: str = Field(
        default="fitfabrica",
        validation_alias=AliasChoices("IMAGE_EDITING_ROOT_PREFIX"),
    )
    product_card_agent_timeout_seconds: float = Field(
        default=90.0,
        gt=0.0,
        le=300.0,
        validation_alias=AliasChoices("PRODUCT_CARD_AGENT_TIMEOUT_SECONDS"),
    )
    product_card_agent_preferred_model: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("PRODUCT_CARD_AGENT_PREFERRED_MODEL"),
    )
    garment_identity_agent_timeout_seconds: float = Field(
        default=90.0,
        gt=0.0,
        le=300.0,
        validation_alias=AliasChoices("GARMENT_IDENTITY_AGENT_TIMEOUT_SECONDS"),
    )
    garment_identity_agent_preferred_model: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GARMENT_IDENTITY_AGENT_PREFERRED_MODEL"),
    )
    garment_identity_agent_minimum_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("GARMENT_IDENTITY_AGENT_MINIMUM_CONFIDENCE"),
    )
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
    crm_sync_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("CRM_SYNC_ENABLED", "HUBSPOT_SYNC_ENABLED"),
    )
    crm_profile_sync_enabled: bool = Field(default=True, validation_alias=AliasChoices("CRM_PROFILE_SYNC_ENABLED"))
    crm_access_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CRM_ACCESS_TOKEN", "HUBSPOT_ACCESS_TOKEN", "HUBSPOT_PRIVATE_APP_TOKEN"),
    )
    crm_base_url: str = "https://api.hubapi.com"
    crm_hubspot_sync_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("HUBSPOT_SYNC_ENABLED", "CRM_SYNC_ENABLED"),
    )

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

    @field_validator("llm_provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in {"fake", "vertex", "gemini_structured"}:
            raise ValueError("LLM_PROVIDER must be one of: fake, vertex, gemini_structured")
        return normalized

    @field_validator("image_editing_provider")
    @classmethod
    def _normalize_image_editing_provider(cls, value: str) -> str:
        normalized = (value or "stub").strip().lower()
        if normalized not in {"stub", "google_genai"}:
            raise ValueError("IMAGE_EDITING_PROVIDER must be one of: stub, google_genai")
        return normalized

    @field_validator("llm_gateway_mode")
    @classmethod
    def _normalize_mode(cls, value: str) -> str:
        return (value or "stub").strip().lower()
