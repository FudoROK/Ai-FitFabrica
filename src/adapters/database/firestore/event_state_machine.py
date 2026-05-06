"""Event/idempotency processing state machine backed by Firestore."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from uuid import uuid4
from typing import Any, Literal

from .storage_primitives import AlreadyExists, require_client_for_write, run_in_transaction, safe_execute
from src.settings import load_settings

EVENT_STATE_RECEIVED = "received"
EVENT_STATE_PROCESSING = "processing"
EVENT_STATE_COMPLETED = "completed"
EVENT_STATE_FAILED = "failed"
PROCESSING_LEASE_SECONDS = 300
DEFAULT_LEASE_RENEW_INTERVAL_SECONDS = 60
DEFAULT_STALE_RECLAIM_SECONDS = 300

logger = logging.getLogger(__name__)

START_DECISION_STARTED = "started"
START_DECISION_RECLAIMED = "reclaimed"
START_DECISION_ALREADY_PROCESSING = "already_processing"
START_DECISION_ALREADY_COMPLETED = "already_completed"


@dataclass
class EventProcessingStartResult:
    decision: Literal["started", "reclaimed", "already_processing", "already_completed"]
    status: str
    should_process: bool
    attempt_count: int
    owner_token: str | None = None


def _lease_duration_seconds() -> int:
    settings = load_settings()
    return int(getattr(settings, "processing_lease_duration_seconds", PROCESSING_LEASE_SECONDS))


def _stale_reclaim_seconds() -> int:
    settings = load_settings()
    return int(getattr(settings, "processing_stale_reclaim_seconds", DEFAULT_STALE_RECLAIM_SECONDS))


def processing_renew_interval_seconds() -> int:
    settings = load_settings()
    return int(getattr(settings, "processing_lease_renew_interval_seconds", DEFAULT_LEASE_RENEW_INTERVAL_SECONDS))


def _lease_expires_at(now: datetime) -> datetime:
    return now + timedelta(seconds=_lease_duration_seconds())


def _attempt_count_from_state(data: dict[str, Any]) -> int:
    return int(data.get("attempt_count") or data.get("attempts") or 0)


def _is_processing_lease_alive(data: dict[str, Any], now: datetime) -> bool:
    lease_expires_at = data.get("processing_expires_at")
    if isinstance(lease_expires_at, datetime):
        return lease_expires_at > now
    started_at = data.get("processing_started_at")
    if isinstance(started_at, datetime):
        return now < (started_at + timedelta(seconds=_stale_reclaim_seconds()))
    return False


def _valid_owner_token(data: dict[str, Any], owner_token: str) -> bool:
    return str(data.get("processing_owner_token") or "") == str(owner_token or "")


def _reclaim_stale_processing(
    *,
    doc_ref: Any,
    now: datetime,
    owner: str | None,
) -> EventProcessingStartResult:
    lease_expires_at = _lease_expires_at(now)
    next_owner_token = uuid4().hex

    def _transactional_reclaim(transaction: Any) -> EventProcessingStartResult:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        status = data.get("status") or EVENT_STATE_RECEIVED
        attempt_count = _attempt_count_from_state(data)

        # completed is terminal for a given event document and cannot be reopened.
        if status == EVENT_STATE_COMPLETED:
            return EventProcessingStartResult(
                decision=START_DECISION_ALREADY_COMPLETED,
                status=EVENT_STATE_COMPLETED,
                should_process=False,
                attempt_count=attempt_count,
            )

        if status == EVENT_STATE_PROCESSING and _is_processing_lease_alive(data, now):
            return EventProcessingStartResult(
                decision=START_DECISION_ALREADY_PROCESSING,
                status=EVENT_STATE_PROCESSING,
                should_process=False,
                attempt_count=attempt_count,
            )

        next_attempt_count = attempt_count + 1
        safe_execute(
            transaction.set,
            doc_ref,
            {
                "status": EVENT_STATE_PROCESSING,
                "processing_started_at": now,
                "processing_expires_at": lease_expires_at,
                "processing_owner": owner,
                "processing_owner_token": next_owner_token,
                "attempt_count": next_attempt_count,
                "updated_at": now,
                "last_error": None,
            },
            merge=True,
        )
        return EventProcessingStartResult(
            decision=START_DECISION_RECLAIMED,
            status=EVENT_STATE_PROCESSING,
            should_process=True,
            attempt_count=next_attempt_count,
            owner_token=next_owner_token,
        )

    return run_in_transaction(_transactional_reclaim)


def start_normalized_event_processing(
    update_key: str,
    channel: str,
    conversation_identity: Any,
    event_identity: Any,
    source: str = "pubsub",
    owner: str | None = None,
) -> EventProcessingStartResult:
    client = require_client_for_write()
    now = datetime.now(timezone.utc)
    lease_expires_at = _lease_expires_at(now)
    doc_ref = client.collection("processed_pubsub_updates").document(update_key)

    payload = {
        "conversation_identity": conversation_identity,
        "event_identity": event_identity,
        "channel": channel,
        "source": source,
        "status": EVENT_STATE_PROCESSING,
        "attempt_count": 1,
        "processing_started_at": now,
        "processing_expires_at": lease_expires_at,
        "processing_owner": owner,
        "processing_owner_token": uuid4().hex,
        "first_received_at": now,
        "updated_at": now,
        "last_error": None,
    }

    try:
        safe_execute(doc_ref.create, payload)
        return EventProcessingStartResult(
            decision=START_DECISION_STARTED,
            status=EVENT_STATE_PROCESSING,
            should_process=True,
            attempt_count=1,
            owner_token=payload["processing_owner_token"],
        )
    except AlreadyExists:
        snapshot = safe_execute(doc_ref.get)

    data = snapshot.to_dict() or {}
    current_status = data.get("status") or EVENT_STATE_RECEIVED
    attempt_count = _attempt_count_from_state(data)

    if current_status == EVENT_STATE_COMPLETED:
        return EventProcessingStartResult(
            decision=START_DECISION_ALREADY_COMPLETED,
            status=EVENT_STATE_COMPLETED,
            should_process=False,
            attempt_count=attempt_count,
        )

    if current_status == EVENT_STATE_PROCESSING and _is_processing_lease_alive(data, now):
        return EventProcessingStartResult(
            decision=START_DECISION_ALREADY_PROCESSING,
            status=EVENT_STATE_PROCESSING,
            should_process=False,
            attempt_count=attempt_count,
        )

    if current_status == EVENT_STATE_PROCESSING:
        return _reclaim_stale_processing(doc_ref=doc_ref, now=now, owner=owner)

    next_attempt_count = attempt_count + 1
    owner_token = uuid4().hex
    safe_execute(
        doc_ref.set,
        {
            "conversation_identity": conversation_identity,
            "event_identity": event_identity,
            "channel": channel,
            "source": source,
            "status": EVENT_STATE_PROCESSING,
            "attempt_count": next_attempt_count,
            "processing_started_at": now,
            "processing_expires_at": lease_expires_at,
            "processing_owner": owner,
            "processing_owner_token": owner_token,
            "updated_at": now,
            "last_error": None,
        },
        merge=True,
    )
    return EventProcessingStartResult(
        decision=START_DECISION_STARTED,
        status=EVENT_STATE_PROCESSING,
        should_process=True,
        attempt_count=next_attempt_count,
        owner_token=owner_token,
    )


def renew_normalized_event_processing_lease(update_key: str, *, owner_token: str) -> bool:
    client = require_client_for_write()
    now = datetime.now(timezone.utc)
    doc_ref = client.collection("processed_pubsub_updates").document(update_key)
    lease_expires_at = _lease_expires_at(now)

    def _transactional_renew(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING:
            return False
        if not _valid_owner_token(data, owner_token):
            return False
        safe_execute(
            transaction.set,
            doc_ref,
            {
                "processing_expires_at": lease_expires_at,
                "updated_at": now,
            },
            merge=True,
        )
        return True

    return run_in_transaction(_transactional_renew)


def is_processing_step_completed(update_key: str, *, step_key: str) -> bool:
    client = require_client_for_write()
    doc_ref = client.collection("processed_pubsub_updates").document(update_key)
    snapshot = safe_execute(doc_ref.get)
    data = snapshot.to_dict() or {}
    completed_steps = data.get("completed_steps")
    return isinstance(completed_steps, dict) and step_key in completed_steps


def mark_processing_step_completed(
    update_key: str,
    *,
    owner_token: str,
    step_key: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    client = require_client_for_write()
    now = datetime.now(timezone.utc)
    doc_ref = client.collection("processed_pubsub_updates").document(update_key)

    def _transactional_mark(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING:
            return False
        if not _valid_owner_token(data, owner_token):
            return False
        completed_steps = data.get("completed_steps") if isinstance(data.get("completed_steps"), dict) else {}
        completed_steps = dict(completed_steps)
        completed_steps[step_key] = {
            "completed_at": now,
            "metadata": metadata or {},
        }
        safe_execute(
            transaction.set,
            doc_ref,
            {
                "completed_steps": completed_steps,
                "updated_at": now,
            },
            merge=True,
        )
        return True

    return run_in_transaction(_transactional_mark)


def complete_normalized_event_processing(update_key: str, *, owner_token: str) -> bool:
    client = require_client_for_write()
    now = datetime.now(timezone.utc)
    doc_ref = client.collection("processed_pubsub_updates").document(update_key)
    def _transactional_complete(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING:
            return False
        if not _valid_owner_token(data, owner_token):
            return False
        safe_execute(
            transaction.set,
            doc_ref,
            {
                # completed is terminal; stale reclaim must never reopen this event.
                "status": EVENT_STATE_COMPLETED,
                "completed_at": now,
                "processing_started_at": None,
                "processing_expires_at": None,
                "processing_owner": None,
                "processing_owner_token": None,
                "updated_at": now,
                "last_error": None,
            },
            merge=True,
        )
        return True

    return run_in_transaction(_transactional_complete)


def fail_normalized_event_processing(update_key: str, *, owner_token: str, error: str) -> bool:
    client = require_client_for_write()
    now = datetime.now(timezone.utc)
    doc_ref = client.collection("processed_pubsub_updates").document(update_key)
    def _transactional_fail(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING:
            return False
        if not _valid_owner_token(data, owner_token):
            return False
        safe_execute(
            transaction.set,
            doc_ref,
            {
                # failed is intentionally retryable by start_normalized_event_processing policy.
                "status": EVENT_STATE_FAILED,
                "failed_at": now,
                "processing_started_at": None,
                "processing_expires_at": None,
                "processing_owner": None,
                "processing_owner_token": None,
                "updated_at": now,
                "last_error": error[:500],
            },
            merge=True,
        )
        return True

    return run_in_transaction(_transactional_fail)
