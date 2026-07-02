from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from .event_state_machine_config import (
    EVENT_STATE_COMPLETED,
    EVENT_STATE_FAILED,
    EVENT_STATE_PROCESSING,
    EVENT_STATE_RECEIVED,
    START_DECISION_ALREADY_COMPLETED,
    START_DECISION_ALREADY_PROCESSING,
    START_DECISION_RECLAIMED,
    START_DECISION_STARTED,
)
from .event_state_machine_helpers import (
    active_processing,
    attempt_count_from_state,
    lease_expires_at,
    terminal_completed,
    valid_owner_token,
)
from .event_state_machine_models import EventProcessingStartResult


def reclaim_stale_processing(*, doc_ref: Any, now: datetime, owner: str | None, safe_execute, run_in_transaction):
    next_expiry = lease_expires_at(now)
    next_owner_token = uuid4().hex

    def _transactional_reclaim(transaction: Any) -> EventProcessingStartResult:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        status = data.get("status") or EVENT_STATE_RECEIVED
        attempt_count = attempt_count_from_state(data)
        if status == EVENT_STATE_COMPLETED:
            return EventProcessingStartResult(
                decision=START_DECISION_ALREADY_COMPLETED,
                status=EVENT_STATE_COMPLETED,
                should_process=False,
                attempt_count=attempt_count,
            )
        if active_processing(data, now):
            return EventProcessingStartResult(
                decision=START_DECISION_ALREADY_PROCESSING,
                status=EVENT_STATE_PROCESSING,
                should_process=False,
                attempt_count=attempt_count,
            )
        next_attempt = attempt_count + 1
        safe_execute(
            transaction.set,
            doc_ref,
            {
                "status": EVENT_STATE_PROCESSING,
                "processing_started_at": now,
                "processing_expires_at": next_expiry,
                "processing_owner": owner,
                "processing_owner_token": next_owner_token,
                "attempt_count": next_attempt,
                "updated_at": now,
                "last_error": None,
            },
            merge=True,
        )
        return EventProcessingStartResult(
            decision=START_DECISION_RECLAIMED,
            status=EVENT_STATE_PROCESSING,
            should_process=True,
            attempt_count=next_attempt,
            owner_token=next_owner_token,
        )

    return run_in_transaction(_transactional_reclaim)


def start_processing_from_existing(
    *,
    data: dict[str, Any],
    doc_ref: Any,
    now: datetime,
    channel: str,
    conversation_identity: Any,
    event_identity: Any,
    source: str,
    owner: str | None,
    safe_execute,
    run_in_transaction,
) -> EventProcessingStartResult:
    current_status = data.get("status") or EVENT_STATE_RECEIVED
    attempt_count = attempt_count_from_state(data)
    if current_status == EVENT_STATE_COMPLETED:
        return EventProcessingStartResult(
            decision=START_DECISION_ALREADY_COMPLETED,
            status=EVENT_STATE_COMPLETED,
            should_process=False,
            attempt_count=attempt_count,
        )
    if active_processing(data, now):
        return EventProcessingStartResult(
            decision=START_DECISION_ALREADY_PROCESSING,
            status=EVENT_STATE_PROCESSING,
            should_process=False,
            attempt_count=attempt_count,
        )
    if current_status == EVENT_STATE_PROCESSING:
        return reclaim_stale_processing(
            doc_ref=doc_ref,
            now=now,
            owner=owner,
            safe_execute=safe_execute,
            run_in_transaction=run_in_transaction,
        )

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
            "processing_expires_at": lease_expires_at(now),
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


def renew_processing_lease(*, doc_ref: Any, owner_token: str, now: datetime, safe_execute, run_in_transaction) -> bool:
    expires_at = lease_expires_at(now)

    def _transactional_renew(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING or not valid_owner_token(data, owner_token):
            return False
        safe_execute(transaction.set, doc_ref, {"processing_expires_at": expires_at, "updated_at": now}, merge=True)
        return True

    return run_in_transaction(_transactional_renew)


def mark_step_completed(*, doc_ref: Any, owner_token: str, step_key: str, metadata: dict[str, Any] | None, now: datetime, safe_execute, run_in_transaction) -> bool:
    def _transactional_mark(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING or not valid_owner_token(data, owner_token):
            return False
        completed_steps = data.get("completed_steps") if isinstance(data.get("completed_steps"), dict) else {}
        next_steps = dict(completed_steps)
        next_steps[step_key] = {"completed_at": now, "metadata": metadata or {}}
        safe_execute(transaction.set, doc_ref, {"completed_steps": next_steps, "updated_at": now}, merge=True)
        return True

    return run_in_transaction(_transactional_mark)


def complete_processing(*, doc_ref: Any, owner_token: str, now: datetime, safe_execute, run_in_transaction) -> bool:
    def _transactional_complete(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING or not valid_owner_token(data, owner_token):
            return False
        safe_execute(
            transaction.set,
            doc_ref,
            {
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


def fail_processing(*, doc_ref: Any, owner_token: str, error: str, now: datetime, safe_execute, run_in_transaction) -> bool:
    def _transactional_fail(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        if data.get("status") != EVENT_STATE_PROCESSING or not valid_owner_token(data, owner_token):
            return False
        safe_execute(
            transaction.set,
            doc_ref,
            {
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
