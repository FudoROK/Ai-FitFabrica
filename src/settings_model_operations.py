"""Operational safeguards and limit settings fields."""
from __future__ import annotations

from pydantic import BaseModel, field_validator


class OperationsSettingsMixin(BaseModel):
    """Rate-limit and lease guard settings."""

    @field_validator("rate_limit_backend", check_fields=False)
    @classmethod
    def _normalize_rate_limit_backend(cls, value: str) -> str:
        normalized = (value or "redis").strip().lower()
        if normalized not in {"redis", "inmemory"}:
            raise ValueError("RATE_LIMIT_BACKEND must be one of: redis, inmemory")
        return normalized

    @field_validator("rate_limit_fail_mode", check_fields=False)
    @classmethod
    def _normalize_rate_limit_fail_mode(cls, value: str) -> str:
        normalized = (value or "closed").strip().lower()
        if normalized not in {"open", "closed"}:
            raise ValueError("RATE_LIMIT_FAIL_MODE must be one of: open, closed")
        return normalized

    @field_validator(
        "processing_lease_duration_seconds",
        "processing_lease_renew_interval_seconds",
        "processing_stale_reclaim_seconds",
        check_fields=False,
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
        check_fields=False,
    )
    @classmethod
    def _validate_positive_rate_limits(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("Rate limit values must be positive integers")
        return int(value)
