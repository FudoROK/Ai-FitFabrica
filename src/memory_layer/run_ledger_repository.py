from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from src.adapters.database.firestore.firestore_async_executor import run_blocking
from src.adapters.database.firestore.firestore_client_factory import (
    get_firestore_client,
    require_client_for_write,
    run_in_transaction,
    safe_execute,
)
from src.memory_layer.domain.memory_run_ledger import (
    MemoryRunAttemptRecord,
    MemoryRunIntent,
    MemoryRunLedgerState,
)

_LEDGER_COLLECTION = "memory_run_ledgers"
_STALE_ATTEMPT_TTL = timedelta(minutes=30)


class MemoryRunBeginDecision:
    def __init__(
        self,
        *,
        proceed: bool,
        state: MemoryRunLedgerState,
        conflict_class: str | None = None,
        reentry_reason: str | None = None,
    ) -> None:
        self.proceed = proceed
        self.state = state
        self.conflict_class = conflict_class
        self.reentry_reason = reentry_reason



def _serialize_attempt(item: MemoryRunAttemptRecord) -> dict[str, Any]:
    payload = asdict(item)
    return {k: v for k, v in payload.items() if v is not None}



def _deserialize_attempt(payload: dict[str, Any]) -> MemoryRunAttemptRecord:
    return MemoryRunAttemptRecord(
        attempt_no=int(payload.get("attempt_no") or 0),
        run_id=str(payload.get("run_id") or ""),
        started_at=payload.get("started_at"),
        ended_at=payload.get("ended_at"),
        outcome=payload.get("outcome"),
        reason_code=payload.get("reason_code"),
        reentry_reason=payload.get("reentry_reason"),
    )



def _deserialize_state(payload: dict[str, Any]) -> MemoryRunLedgerState:
    return MemoryRunLedgerState(
        intent_id=str(payload.get("intent_id") or ""),
        run_id=str(payload.get("run_id") or ""),
        attempt_no=int(payload.get("attempt_no") or 0),
        lead_id=str(payload.get("lead_id") or ""),
        local_day_key=str(payload.get("local_day_key") or ""),
        window_id=str(payload.get("window_id") or ""),
        pipeline_version=str(payload.get("pipeline_version") or ""),
        current_stage=payload.get("current_stage"),
        stage_statuses={str(k): str(v) for k, v in dict(payload.get("stage_statuses") or {}).items()},
        stage_reason_codes={str(k): str(v) for k, v in dict(payload.get("stage_reason_codes") or {}).items()},
        final_outcome=payload.get("final_outcome"),
        reason_code=payload.get("reason_code"),
        rolling_version=payload.get("rolling_version"),
        rolling_hash=payload.get("rolling_hash"),
        artifact_id=payload.get("artifact_id"),
        conflict_class=payload.get("conflict_class"),
        partial_effect_detected=bool(payload.get("partial_effect_detected", False)),
        recovered=bool(payload.get("recovered", False)),
        in_progress=bool(payload.get("in_progress", False)),
        reentry_reason=payload.get("reentry_reason"),
        created_at=payload.get("created_at"),
        updated_at=payload.get("updated_at"),
        last_attempt_started_at=payload.get("last_attempt_started_at"),
        last_attempt_finished_at=payload.get("last_attempt_finished_at"),
        attempt_history=[
            _deserialize_attempt(item)
            for item in list(payload.get("attempt_history") or [])
            if isinstance(item, dict)
        ],
    )



def _serialize_state(state: MemoryRunLedgerState) -> dict[str, Any]:
    payload = {
        "intent_id": state.intent_id,
        "run_id": state.run_id,
        "attempt_no": state.attempt_no,
        "lead_id": state.lead_id,
        "local_day_key": state.local_day_key,
        "window_id": state.window_id,
        "pipeline_version": state.pipeline_version,
        "current_stage": state.current_stage,
        "stage_statuses": dict(state.stage_statuses),
        "stage_reason_codes": dict(state.stage_reason_codes),
        "final_outcome": state.final_outcome,
        "reason_code": state.reason_code,
        "rolling_version": state.rolling_version,
        "rolling_hash": state.rolling_hash,
        "artifact_id": state.artifact_id,
        "conflict_class": state.conflict_class,
        "partial_effect_detected": state.partial_effect_detected,
        "recovered": state.recovered,
        "in_progress": state.in_progress,
        "reentry_reason": state.reentry_reason,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "last_attempt_started_at": state.last_attempt_started_at,
        "last_attempt_finished_at": state.last_attempt_finished_at,
        "attempt_history": [_serialize_attempt(item) for item in state.attempt_history],
    }
    return {k: v for k, v in payload.items() if v is not None}



def _build_initial_state(intent: MemoryRunIntent, now: datetime) -> MemoryRunLedgerState:
    run_id = uuid4().hex
    attempt = MemoryRunAttemptRecord(attempt_no=1, run_id=run_id, started_at=now)
    return MemoryRunLedgerState(
        intent_id=intent.intent_id,
        run_id=run_id,
        attempt_no=1,
        lead_id=intent.lead_id,
        local_day_key=intent.local_day_key,
        window_id=intent.window_id,
        pipeline_version=intent.pipeline_version,
        current_stage="load_context",
        stage_statuses={"load_context": "started"},
        in_progress=True,
        created_at=now,
        updated_at=now,
        last_attempt_started_at=now,
        attempt_history=[attempt],
    )


class FirestoreMemoryRunLedgerRepository:
    def _doc_ref(self, *, intent_id: str):
        return require_client_for_write().collection(_LEDGER_COLLECTION).document(intent_id)

    async def get(self, *, intent_id: str) -> MemoryRunLedgerState | None:
        return await run_blocking(self._get_sync, intent_id)

    def _get_sync(self, intent_id: str) -> MemoryRunLedgerState | None:
        if not intent_id:
            return None
        client = get_firestore_client()
        if not client:
            return None
        snapshot = safe_execute(client.collection(_LEDGER_COLLECTION).document(intent_id).get)
        if not snapshot or not getattr(snapshot, "exists", False):
            return None
        return _deserialize_state(snapshot.to_dict() or {})

    async def begin_attempt(self, *, intent: MemoryRunIntent, now: datetime) -> MemoryRunBeginDecision:
        return await run_blocking(self._begin_attempt_sync, intent, now)

    def _begin_attempt_sync(self, intent: MemoryRunIntent, now: datetime) -> MemoryRunBeginDecision:
        doc_ref = self._doc_ref(intent_id=intent.intent_id)

        def _work(transaction):
            snapshot = safe_execute(doc_ref.get, transaction=transaction)
            if not snapshot or not getattr(snapshot, "exists", False):
                state = _build_initial_state(intent, now)
                safe_execute(transaction.set, doc_ref, _serialize_state(state))
                return MemoryRunBeginDecision(proceed=True, state=state, reentry_reason="new_intent")

            current = _deserialize_state(snapshot.to_dict() or {})

            if current.final_outcome == "success":
                current.conflict_class = "duplicate_complete"
                current.updated_at = now
                safe_execute(transaction.set, doc_ref, _serialize_state(current), merge=True)
                return MemoryRunBeginDecision(proceed=False, state=current, conflict_class="duplicate_complete")

            if current.in_progress:
                started_at = current.last_attempt_started_at or current.updated_at or current.created_at
                if isinstance(started_at, datetime) and now - started_at <= _STALE_ATTEMPT_TTL:
                    current.conflict_class = "conflict_in_progress"
                    current.updated_at = now
                    safe_execute(transaction.set, doc_ref, _serialize_state(current), merge=True)
                    return MemoryRunBeginDecision(proceed=False, state=current, conflict_class="conflict_in_progress")

            if current.partial_effect_detected and current.current_stage not in {
                "daily_synced",
                "finalize",
            }:
                current.conflict_class = "conflict_unknown"
                current.updated_at = now
                safe_execute(transaction.set, doc_ref, _serialize_state(current), merge=True)
                return MemoryRunBeginDecision(proceed=False, state=current, conflict_class="conflict_unknown")

            next_attempt = current.attempt_no + 1
            reentry_reason = "retry_after_stale_in_progress" if current.in_progress else "retry_after_failure"
            current.attempt_no = next_attempt
            current.in_progress = True
            current.recovered = bool(current.partial_effect_detected)
            current.reentry_reason = reentry_reason
            current.conflict_class = None
            current.updated_at = now
            current.last_attempt_started_at = now
            current.current_stage = current.current_stage or "load_context"
            current.stage_statuses[current.current_stage] = "started"
            current.attempt_history.append(
                MemoryRunAttemptRecord(
                    attempt_no=next_attempt,
                    run_id=current.run_id,
                    started_at=now,
                    reentry_reason=reentry_reason,
                )
            )
            safe_execute(transaction.set, doc_ref, _serialize_state(current), merge=True)
            return MemoryRunBeginDecision(proceed=True, state=current, reentry_reason=reentry_reason)

        return run_in_transaction(_work)

    async def mark_stage(
        self,
        *,
        intent_id: str,
        stage: str,
        status: str,
        now: datetime,
        reason_code: str | None,
        rolling_version: int | None = None,
        rolling_hash: str | None = None,
        artifact_id: str | None = None,
    ) -> MemoryRunLedgerState | None:
        return await run_blocking(
            self._mark_stage_sync,
            intent_id,
            stage,
            status,
            now,
            reason_code,
            rolling_version,
            rolling_hash,
            artifact_id,
        )

    def _mark_stage_sync(
        self,
        intent_id: str,
        stage: str,
        status: str,
        now: datetime,
        reason_code: str | None,
        rolling_version: int | None,
        rolling_hash: str | None,
        artifact_id: str | None,
    ) -> MemoryRunLedgerState | None:
        doc_ref = self._doc_ref(intent_id=intent_id)

        def _work(transaction):
            snapshot = safe_execute(doc_ref.get, transaction=transaction)
            if not snapshot or not getattr(snapshot, "exists", False):
                return None
            state = _deserialize_state(snapshot.to_dict() or {})
            state.current_stage = stage
            state.stage_statuses[stage] = status
            if reason_code:
                state.stage_reason_codes[stage] = reason_code
            state.updated_at = now
            if reason_code:
                state.reason_code = reason_code
            if rolling_version is not None:
                state.rolling_version = rolling_version
            if rolling_hash:
                state.rolling_hash = rolling_hash
            if artifact_id:
                state.artifact_id = artifact_id
            safe_execute(transaction.set, doc_ref, _serialize_state(state), merge=True)
            return state

        return run_in_transaction(_work)

    async def mark_partial_effect(
        self,
        *,
        intent_id: str,
        now: datetime,
        reason_code: str,
    ) -> MemoryRunLedgerState | None:
        return await run_blocking(self._mark_partial_effect_sync, intent_id, now, reason_code)

    def _mark_partial_effect_sync(self, intent_id: str, now: datetime, reason_code: str) -> MemoryRunLedgerState | None:
        doc_ref = self._doc_ref(intent_id=intent_id)

        def _work(transaction):
            snapshot = safe_execute(doc_ref.get, transaction=transaction)
            if not snapshot or not getattr(snapshot, "exists", False):
                return None
            state = _deserialize_state(snapshot.to_dict() or {})
            state.partial_effect_detected = True
            state.reason_code = reason_code
            state.updated_at = now
            safe_execute(transaction.set, doc_ref, _serialize_state(state), merge=True)
            return state

        return run_in_transaction(_work)

    async def finalize(
        self,
        *,
        intent_id: str,
        final_outcome: str,
        now: datetime,
        reason_code: str | None,
        conflict_class: str | None,
        partial_effect_detected: bool,
        recovered: bool,
    ) -> MemoryRunLedgerState | None:
        return await run_blocking(
            self._finalize_sync,
            intent_id,
            final_outcome,
            now,
            reason_code,
            conflict_class,
            partial_effect_detected,
            recovered,
        )

    def _finalize_sync(
        self,
        intent_id: str,
        final_outcome: str,
        now: datetime,
        reason_code: str | None,
        conflict_class: str | None,
        partial_effect_detected: bool,
        recovered: bool,
    ) -> MemoryRunLedgerState | None:
        doc_ref = self._doc_ref(intent_id=intent_id)

        def _work(transaction):
            snapshot = safe_execute(doc_ref.get, transaction=transaction)
            if not snapshot or not getattr(snapshot, "exists", False):
                return None
            state = _deserialize_state(snapshot.to_dict() or {})
            state.final_outcome = final_outcome
            state.reason_code = reason_code
            state.conflict_class = conflict_class
            state.partial_effect_detected = partial_effect_detected
            state.recovered = recovered
            state.in_progress = False
            state.updated_at = now
            state.last_attempt_finished_at = now
            for idx in range(len(state.attempt_history) - 1, -1, -1):
                attempt = state.attempt_history[idx]
                if attempt.attempt_no == state.attempt_no and attempt.ended_at is None:
                    state.attempt_history[idx] = MemoryRunAttemptRecord(
                        attempt_no=attempt.attempt_no,
                        run_id=attempt.run_id,
                        started_at=attempt.started_at,
                        ended_at=now,
                        outcome=final_outcome,
                        reason_code=reason_code,
                        reentry_reason=attempt.reentry_reason,
                    )
                    break
            safe_execute(transaction.set, doc_ref, _serialize_state(state), merge=True)
            return state

        return run_in_transaction(_work)


class InMemoryMemoryRunLedgerRepository:
    def __init__(self) -> None:
        self._store: dict[str, MemoryRunLedgerState] = {}

    async def get(self, *, intent_id: str) -> MemoryRunLedgerState | None:
        return self._store.get(intent_id)

    async def begin_attempt(self, *, intent: MemoryRunIntent, now: datetime) -> MemoryRunBeginDecision:
        current = self._store.get(intent.intent_id)
        if current is None:
            state = _build_initial_state(intent, now)
            self._store[intent.intent_id] = state
            return MemoryRunBeginDecision(proceed=True, state=state, reentry_reason="new_intent")

        if current.final_outcome == "success":
            current.conflict_class = "duplicate_complete"
            current.updated_at = now
            return MemoryRunBeginDecision(proceed=False, state=current, conflict_class="duplicate_complete")

        if current.in_progress:
            started_at = current.last_attempt_started_at or current.updated_at or current.created_at
            if isinstance(started_at, datetime) and now - started_at <= _STALE_ATTEMPT_TTL:
                current.conflict_class = "conflict_in_progress"
                current.updated_at = now
                return MemoryRunBeginDecision(proceed=False, state=current, conflict_class="conflict_in_progress")

        if current.partial_effect_detected and current.current_stage not in {
            "daily_synced",
            "finalize",
        }:
            current.conflict_class = "conflict_unknown"
            current.updated_at = now
            return MemoryRunBeginDecision(proceed=False, state=current, conflict_class="conflict_unknown")

        next_attempt = current.attempt_no + 1
        reentry_reason = "retry_after_stale_in_progress" if current.in_progress else "retry_after_failure"
        current.attempt_no = next_attempt
        current.in_progress = True
        current.recovered = bool(current.partial_effect_detected)
        current.reentry_reason = reentry_reason
        current.conflict_class = None
        current.updated_at = now
        current.last_attempt_started_at = now
        current.current_stage = current.current_stage or "load_context"
        current.stage_statuses[current.current_stage] = "started"
        current.attempt_history.append(
            MemoryRunAttemptRecord(
                attempt_no=next_attempt,
                run_id=current.run_id,
                started_at=now,
                reentry_reason=reentry_reason,
            )
        )
        return MemoryRunBeginDecision(proceed=True, state=current, reentry_reason=reentry_reason)

    async def mark_stage(
        self,
        *,
        intent_id: str,
        stage: str,
        status: str,
        now: datetime,
        reason_code: str | None,
        rolling_version: int | None = None,
        rolling_hash: str | None = None,
        artifact_id: str | None = None,
    ) -> MemoryRunLedgerState | None:
        state = self._store.get(intent_id)
        if state is None:
            return None
        state.current_stage = stage
        state.stage_statuses[stage] = status
        if reason_code:
            state.stage_reason_codes[stage] = reason_code
        state.updated_at = now
        if reason_code:
            state.reason_code = reason_code
        if rolling_version is not None:
            state.rolling_version = rolling_version
        if rolling_hash:
            state.rolling_hash = rolling_hash
        if artifact_id:
            state.artifact_id = artifact_id
        return state

    async def mark_partial_effect(self, *, intent_id: str, now: datetime, reason_code: str) -> MemoryRunLedgerState | None:
        state = self._store.get(intent_id)
        if state is None:
            return None
        state.partial_effect_detected = True
        state.reason_code = reason_code
        state.updated_at = now
        return state

    async def finalize(
        self,
        *,
        intent_id: str,
        final_outcome: str,
        now: datetime,
        reason_code: str | None,
        conflict_class: str | None,
        partial_effect_detected: bool,
        recovered: bool,
    ) -> MemoryRunLedgerState | None:
        state = self._store.get(intent_id)
        if state is None:
            return None
        state.final_outcome = final_outcome
        state.reason_code = reason_code
        state.conflict_class = conflict_class
        state.partial_effect_detected = partial_effect_detected
        state.recovered = recovered
        state.in_progress = False
        state.updated_at = now
        state.last_attempt_finished_at = now
        for idx in range(len(state.attempt_history) - 1, -1, -1):
            attempt = state.attempt_history[idx]
            if attempt.attempt_no == state.attempt_no and attempt.ended_at is None:
                state.attempt_history[idx] = MemoryRunAttemptRecord(
                    attempt_no=attempt.attempt_no,
                    run_id=attempt.run_id,
                    started_at=attempt.started_at,
                    ended_at=now,
                    outcome=final_outcome,
                    reason_code=reason_code,
                    reentry_reason=attempt.reentry_reason,
                )
                break
        return state


__all__ = [
    "FirestoreMemoryRunLedgerRepository",
    "InMemoryMemoryRunLedgerRepository",
    "MemoryRunBeginDecision",
]
