from __future__ import annotations

from dataclasses import dataclass

from src.settings import load_settings


@dataclass(frozen=True)
class FeatureFlags:
    enable_profile_runtime: bool
    enable_search_engine_discovery: bool

    def reply_runtime_enabled(self) -> bool:
        return bool(self.enable_profile_runtime)

    def search_engine_discovery_enabled(self) -> bool:
        return bool(self.enable_search_engine_discovery)


def resolve_feature_flags(settings=None) -> FeatureFlags:
    runtime_settings = settings or load_settings()
    return FeatureFlags(
        enable_profile_runtime=bool(getattr(runtime_settings, "enable_profile_runtime", True)),
        enable_search_engine_discovery=bool(getattr(runtime_settings, "enable_search_engine_discovery", False)),
    )
