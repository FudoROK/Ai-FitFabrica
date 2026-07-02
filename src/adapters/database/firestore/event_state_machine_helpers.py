from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .event_state_machine_config import (
    EVENT_STATE_COMPLETED,
    EVENT_STATE_PROCESSING,
    lease_duration_seconds,
    stale_reclaim_seconds,
)


def lease_expires_at(now: datetime) -> datetime:
    return now + timedelta(seconds=lease_duration_seconds())


def attempt_count_from_state(data: dict[str, Any]) -> int:
    return int(data.get("attempt_count") or data.get("attempts") or 0)


def is_processing_lease_alive(data: dict[str, Any], now: datetime) -> bool:
    expires_at = data.get("processing_expires_at")
    if isinstance(expires_at, datetime):
        return expires_at > now
    started_at = data.get("processing_started_at")
    if isinstance(started_at, datetime):
        return now < (started_at + timedelta(seconds=stale_reclaim_seconds()))
    return False


def valid_owner_token(data: dict[str, Any], owner_token: str) -> bool:
    return str(data.get("processing_owner_token") or "") == str(owner_token or "")


def terminal_completed(data: dict[str, Any]) -> bool:
    return (data.get("status") or "") == EVENT_STATE_COMPLETED


def active_processing(data: dict[str, Any], now: datetime) -> bool:
    return (data.get("status") or "") == EVENT_STATE_PROCESSING and is_processing_lease_alive(data, now)
