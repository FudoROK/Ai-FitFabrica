"""Centralized, validated application settings (single env source)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from .settings_contracts import CRMSettings, LLMSettings
from .settings_model import SettingsModel
from .settings_runtime import bind_settings_loader, build_crm_settings, build_llm_settings, validate_settings


class Settings(SettingsModel, BaseSettings):
    """Strongly typed application configuration with derived accessors."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow")

    @property
    def llm(self) -> LLMSettings:
        return build_llm_settings(self)

    @property
    def crm(self) -> CRMSettings:
        return build_crm_settings(self)


load_settings = bind_settings_loader(Settings)
