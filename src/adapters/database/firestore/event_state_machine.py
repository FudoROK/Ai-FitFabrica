"""Event/idempotency processing state machine backed by Firestore."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .storage_primitives import AlreadyExists, require_client_for_write, run_in_transaction, safe_execute
from .event_state_machine_config import (
    DEFAULT_LEASE_RENEW_INTERVAL_SECONDS,
    DEFAULT_STALE_RECLAIM_SECONDS,
    EVENT_STATE_COMPLETED,
    EVENT_STATE_FAILED,
    EVENT_STATE_PROCESSING,
    EVENT_STATE_RECEIVED,
    PROCESSING_LEASE_SECONDS,
    START_DECISION_ALREADY_COMPLETED,
    START_DECISION_ALREADY_PROCESSING,
    START_DECISION_RECLAIMED,
    START_DECISION_STARTED,
    lease_duration_seconds as _lease_duration_seconds,
    processing_renew_interval_seconds,
    stale_reclaim_seconds as _stale_reclaim_seconds,
)
from .event_state_machine_helpers import (
    attempt_count_from_state as _attempt_count_from_state,
    is_processing_lease_alive as _is_processing_lease_alive,
    lease_expires_at as _lease_expires_at,
    valid_owner_token as _valid_owner_token,
)
from .event_state_machine_models import EventProcessingStartResult
from .event_state_machine_transitions import (
    complete_processing,
    fail_processing,
    mark_step_completed,
    reclaim_stale_processing as _reclaim_stale_processing,
    renew_processing_lease,
    start_processing_from_existing,
)


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
    return start_processing_from_existing(
        data=snapshot.to_dict() or {},
        doc_ref=doc_ref,
        now=now,
        channel=channel,
        conversation_identity=conversation_identity,
        event_identity=event_identity,
        source=source,
        owner=owner,
        safe_execute=safe_execute,
        run_in_transaction=run_in_transaction,
    )


def renew_normalized_event_processing_lease(update_key: str, *, owner_token: str) -> bool:
    client = require_client_for_write()
    return renew_processing_lease(
        doc_ref=client.collection("processed_pubsub_updates").document(update_key),
        owner_token=owner_token,
        now=datetime.now(timezone.utc),
        safe_execute=safe_execute,
        run_in_transaction=run_in_transaction,
    )


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
    return mark_step_completed(
        doc_ref=client.collection("processed_pubsub_updates").document(update_key),
        owner_token=owner_token,
        step_key=step_key,
        metadata=metadata,
        now=datetime.now(timezone.utc),
        safe_execute=safe_execute,
        run_in_transaction=run_in_transaction,
    )


def complete_normalized_event_processing(update_key: str, *, owner_token: str) -> bool:
    client = require_client_for_write()
    return complete_processing(
        doc_ref=client.collection("processed_pubsub_updates").document(update_key),
        owner_token=owner_token,
        now=datetime.now(timezone.utc),
        safe_execute=safe_execute,
        run_in_transaction=run_in_transaction,
    )


def fail_normalized_event_processing(update_key: str, *, owner_token: str, error: str) -> bool:
    client = require_client_for_write()
    return fail_processing(
        doc_ref=client.collection("processed_pubsub_updates").document(update_key),
        owner_token=owner_token,
        error=error,
        now=datetime.now(timezone.utc),
        safe_execute=safe_execute,
        run_in_transaction=run_in_transaction,
    )


__all__ = [
    "AlreadyExists",
    "DEFAULT_LEASE_RENEW_INTERVAL_SECONDS",
    "DEFAULT_STALE_RECLAIM_SECONDS",
    "EVENT_STATE_COMPLETED",
    "EVENT_STATE_FAILED",
    "EVENT_STATE_PROCESSING",
    "EVENT_STATE_RECEIVED",
    "EventProcessingStartResult",
    "PROCESSING_LEASE_SECONDS",
    "START_DECISION_ALREADY_COMPLETED",
    "START_DECISION_ALREADY_PROCESSING",
    "START_DECISION_RECLAIMED",
    "START_DECISION_STARTED",
    "_attempt_count_from_state",
    "_is_processing_lease_alive",
    "_lease_duration_seconds",
    "_lease_expires_at",
    "_reclaim_stale_processing",
    "_stale_reclaim_seconds",
    "_valid_owner_token",
    "complete_normalized_event_processing",
    "fail_normalized_event_processing",
    "is_processing_step_completed",
    "mark_processing_step_completed",
    "processing_renew_interval_seconds",
    "renew_normalized_event_processing_lease",
    "start_normalized_event_processing",
]
