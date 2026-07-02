from __future__ import annotations

from src.settings import load_settings

EVENT_STATE_RECEIVED = "received"
EVENT_STATE_PROCESSING = "processing"
EVENT_STATE_COMPLETED = "completed"
EVENT_STATE_FAILED = "failed"
PROCESSING_LEASE_SECONDS = 300
DEFAULT_LEASE_RENEW_INTERVAL_SECONDS = 60
DEFAULT_STALE_RECLAIM_SECONDS = 300

START_DECISION_STARTED = "started"
START_DECISION_RECLAIMED = "reclaimed"
START_DECISION_ALREADY_PROCESSING = "already_processing"
START_DECISION_ALREADY_COMPLETED = "already_completed"


def lease_duration_seconds() -> int:
    settings = load_settings()
    return int(getattr(settings, "processing_lease_duration_seconds", PROCESSING_LEASE_SECONDS))


def stale_reclaim_seconds() -> int:
    settings = load_settings()
    return int(getattr(settings, "processing_stale_reclaim_seconds", DEFAULT_STALE_RECLAIM_SECONDS))


def processing_renew_interval_seconds() -> int:
    settings = load_settings()
    return int(getattr(settings, "processing_lease_renew_interval_seconds", DEFAULT_LEASE_RENEW_INTERVAL_SECONDS))
