from __future__ import annotations

from dataclasses import dataclass

from src.settings import load_settings


@dataclass(frozen=True)
class FeatureFlags:
    enable_profile_runtime: bool
    enable_memory_profile: bool

    @property
    def memory_profile_runtime_enabled(self) -> bool:
        return bool(self.enable_profile_runtime and self.enable_memory_profile)

    def reply_runtime_enabled(self) -> bool:
        return bool(self.enable_profile_runtime)

    def memory_runtime_enabled(self) -> bool:
        return bool(self.enable_profile_runtime and self.enable_memory_profile)


def resolve_feature_flags(settings=None) -> FeatureFlags:
    runtime_settings = settings or load_settings()
    return FeatureFlags(
        enable_profile_runtime=bool(getattr(runtime_settings, "enable_profile_runtime", True)),
        enable_memory_profile=bool(getattr(runtime_settings, "enable_memory_profile", True)),
    )
