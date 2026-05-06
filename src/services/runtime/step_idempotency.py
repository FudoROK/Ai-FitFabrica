"""Unified step-level idempotency policy for side effects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.adapters.database.firestore.event_state_machine import is_processing_step_completed, mark_processing_step_completed
from src.adapters.database.firestore.storage_primitives import require_client_for_write, safe_execute
from .step_keys import StepKeys


@dataclass(frozen=True)
class StepContext:
    """Execution context used to resolve step-idempotency scope."""

    event_key: str | None = None
    owner_token: str | None = None
    lead_id: str | None = None
    daily_date: str | None = None
    rolling_version: int | None = None
    rolling_hash: str | None = None


@dataclass(frozen=True)
class StepScope:
    kind: str
    key: str


class StepIdempotencyPolicy:
    """Single policy layer for canonical keys, scopes and check/mark semantics."""

    _SCOPED_MARKERS_COLLECTION = "crm_step_markers"

    def resolve_step_key(self, *, step: str, channel: str | None = None) -> str:
        if step == StepKeys.SEND_REPLY:
            return StepKeys.send_reply(channel=channel or "")
        if step == StepKeys.CRM_FIND_OR_CREATE_CONTACT:
            return StepKeys.CRM_FIND_OR_CREATE_CONTACT
        if step == StepKeys.CRM_BIND_CONTACT_REF:
            return StepKeys.CRM_BIND_CONTACT_REF
        if step == StepKeys.CRM_UPDATE_CONTACT_PROFILE:
            return StepKeys.CRM_UPDATE_CONTACT_PROFILE
        if step == StepKeys.CRM_SYNC_MEMORY:
            return StepKeys.CRM_SYNC_MEMORY
        raise ValueError(f"Unknown canonical step: {step}")

    def resolve_scope(
        self,
        *,
        step: str,
        context: StepContext,
        scope_override: str | None = None,
    ) -> StepScope | None:
        if scope_override:
            return StepScope(kind="scoped", key=str(scope_override))

        if step == StepKeys.SEND_REPLY:
            if not context.event_key:
                return None
            return StepScope(kind="event", key=context.event_key)

        if step in {
            StepKeys.CRM_FIND_OR_CREATE_CONTACT,
            StepKeys.CRM_BIND_CONTACT_REF,
            StepKeys.CRM_UPDATE_CONTACT_PROFILE,
        }:
            if context.event_key:
                return StepScope(kind="event", key=context.event_key)
            if context.lead_id:
                return StepScope(kind="scoped", key=f"lead:{context.lead_id}")
            return None

        if step == StepKeys.CRM_SYNC_MEMORY:
            if context.lead_id and context.rolling_version is not None and context.rolling_hash:
                return StepScope(
                    kind="scoped",
                    key=f"memory:{context.lead_id}:{context.rolling_version}:{context.rolling_hash}",
                )
            return None

        raise ValueError(f"Unknown canonical step: {step}")

    def is_step_completed(
        self,
        *,
        step: str,
        context: StepContext,
        channel: str | None = None,
        scope_override: str | None = None,
    ) -> bool:
        step_key = self.resolve_step_key(step=step, channel=channel)
        scope = self.resolve_scope(step=step, context=context, scope_override=scope_override)
        if not scope:
            return False

        if scope.kind == "event":
            return is_processing_step_completed(scope.key, step_key=step_key)

        return self._is_scoped_step_completed(scope_key=scope.key, step_key=step_key)

    def mark_step_completed(
        self,
        *,
        step: str,
        context: StepContext,
        metadata: dict[str, Any] | None = None,
        channel: str | None = None,
        scope_override: str | None = None,
    ) -> bool:
        step_key = self.resolve_step_key(step=step, channel=channel)
        scope = self.resolve_scope(step=step, context=context, scope_override=scope_override)
        if not scope:
            return False

        if scope.kind == "event":
            if not context.owner_token:
                return False
            return mark_processing_step_completed(
                scope.key,
                owner_token=context.owner_token,
                step_key=step_key,
                metadata=metadata or {},
            )

        return self._mark_scoped_step_completed(scope_key=scope.key, step_key=step_key, metadata=metadata)

    def _is_scoped_step_completed(self, *, scope_key: str, step_key: str) -> bool:
        if not scope_key or not step_key:
            return False
        doc_ref = require_client_for_write().collection(self._SCOPED_MARKERS_COLLECTION).document(
            f"{scope_key}:{step_key}"
        )
        snapshot = safe_execute(doc_ref.get)
        return bool(snapshot and getattr(snapshot, "exists", False))

    def _mark_scoped_step_completed(
        self,
        *,
        scope_key: str,
        step_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if not scope_key or not step_key:
            return False
        doc_ref = require_client_for_write().collection(self._SCOPED_MARKERS_COLLECTION).document(
            f"{scope_key}:{step_key}"
        )
        payload = {
            "scope_key": scope_key,
            "step_key": step_key,
            "metadata": metadata or {},
            "completed_at": datetime.now(timezone.utc),
        }
        try:
            safe_execute(doc_ref.create, payload)
            return True
        except Exception:
            snapshot = safe_execute(doc_ref.get)
            return bool(snapshot and getattr(snapshot, "exists", False))
