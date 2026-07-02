"""Reusable typed settings model with validation rules."""
from __future__ import annotations

from pydantic import BaseModel

from .settings_model_app import AppSettingsMixin
from .settings_model_operations import OperationsSettingsMixin
from .settings_model_platform import PlatformSettingsMixin
from .settings_model_providers import ProviderSettingsMixin
from .settings_model_try_on import TryOnSettingsMixin


class SettingsModel(
    AppSettingsMixin,
    ProviderSettingsMixin,
    TryOnSettingsMixin,
    PlatformSettingsMixin,
    OperationsSettingsMixin,
    BaseModel,
):
    """Shared settings field model inherited by the env-backed Settings class."""
