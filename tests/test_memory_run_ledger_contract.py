from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from src.memory_layer.domain.memory_run_ledger import MemoryRunIntent
from src.memory_layer.run_ledger_repository import InMemoryMemoryRunLedgerRepository


def test_conflict_in_progress_for_same_intent() -> None:
    repo = InMemoryMemoryRunLedgerRepository()
    intent = MemoryRunIntent(
        lead_id="lead-1",
        local_day_key="2025-01-01",
        window_id="window-1",
        pipeline_version="memory_pipeline_v2",
    )
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)

    first = asyncio.run(repo.begin_attempt(intent=intent, now=now))
    second = asyncio.run(repo.begin_attempt(intent=intent, now=now + timedelta(minutes=5)))

    assert first.proceed is True
    assert second.proceed is False
    assert second.conflict_class == "conflict_in_progress"


def test_duplicate_complete_requires_successful_final_outcome() -> None:
    repo = InMemoryMemoryRunLedgerRepository()
    intent = MemoryRunIntent(
        lead_id="lead-1",
        local_day_key="2025-01-01",
        window_id="window-1",
        pipeline_version="memory_pipeline_v2",
    )
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)

    started = asyncio.run(repo.begin_attempt(intent=intent, now=now))
    assert started.proceed is True

    finalized = asyncio.run(
        repo.finalize(
            intent_id=intent.intent_id,
            final_outcome="success",
            now=now + timedelta(minutes=1),
            reason_code=None,
            conflict_class=None,
            partial_effect_detected=False,
            recovered=False,
        )
    )
    assert finalized is not None

    duplicate = asyncio.run(repo.begin_attempt(intent=intent, now=now + timedelta(minutes=2)))
    assert duplicate.proceed is False
    assert duplicate.conflict_class == "duplicate_complete"


def test_conflict_unknown_when_partial_effect_not_recoverable() -> None:
    repo = InMemoryMemoryRunLedgerRepository()
    intent = MemoryRunIntent(
        lead_id="lead-1",
        local_day_key="2025-01-01",
        window_id="window-1",
        pipeline_version="memory_pipeline_v2",
    )
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)

    started = asyncio.run(repo.begin_attempt(intent=intent, now=now))
    assert started.proceed is True

    asyncio.run(repo.mark_partial_effect(intent_id=intent.intent_id, now=now + timedelta(minutes=1), reason_code="boom"))
    asyncio.run(
        repo.mark_stage(
            intent_id=intent.intent_id,
            stage="apply_write",
            status="failed",
            now=now + timedelta(minutes=1),
            reason_code="boom",
        )
    )
    asyncio.run(
        repo.finalize(
            intent_id=intent.intent_id,
            final_outcome="failed",
            now=now + timedelta(minutes=2),
            reason_code="boom",
            conflict_class="conflict_unknown",
            partial_effect_detected=True,
            recovered=False,
        )
    )

    decision = asyncio.run(repo.begin_attempt(intent=intent, now=now + timedelta(minutes=3)))
    assert decision.proceed is False
    assert decision.conflict_class == "conflict_unknown"


def test_safe_reentry_recovery_from_stale_in_progress_on_daily_stage() -> None:
    repo = InMemoryMemoryRunLedgerRepository()
    intent = MemoryRunIntent(
        lead_id="lead-1",
        local_day_key="2025-01-01",
        window_id="window-1",
        pipeline_version="memory_pipeline_v2",
    )
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)

    first = asyncio.run(repo.begin_attempt(intent=intent, now=now))
    assert first.proceed is True
    asyncio.run(repo.mark_partial_effect(intent_id=intent.intent_id, now=now + timedelta(minutes=1), reason_code="crm_timeout"))
    asyncio.run(
        repo.mark_stage(
            intent_id=intent.intent_id,
            stage="daily_synced",
            status="started",
            now=now + timedelta(minutes=1),
            reason_code="crm_timeout",
        )
    )

    state = asyncio.run(repo.get(intent_id=intent.intent_id))
    assert state is not None
    state.last_attempt_started_at = now - timedelta(hours=1)

    retry = asyncio.run(repo.begin_attempt(intent=intent, now=now + timedelta(hours=1, minutes=1)))
    assert retry.proceed is True
    assert retry.state.attempt_no == 2
    assert retry.state.recovered is True


def test_idempotency_conflict_state_stays_classified_and_not_dirty_unknown() -> None:
    repo = InMemoryMemoryRunLedgerRepository()
    intent = MemoryRunIntent(
        lead_id="lead-1",
        local_day_key="2025-01-01",
        window_id="window-1",
        pipeline_version="memory_pipeline_v2",
    )
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)

    started = asyncio.run(repo.begin_attempt(intent=intent, now=now))
    assert started.proceed is True
    asyncio.run(
        repo.mark_stage(
            intent_id=intent.intent_id,
            stage="apply_write",
            status="failed",
            now=now + timedelta(minutes=1),
            reason_code="idempotency_conflict",
        )
    )
    finalized = asyncio.run(
        repo.finalize(
            intent_id=intent.intent_id,
            final_outcome="failed",
            now=now + timedelta(minutes=1),
            reason_code="idempotency_conflict",
            conflict_class="idempotency_conflict",
            partial_effect_detected=False,
            recovered=False,
        )
    )

    assert finalized is not None
    assert finalized.reason_code == "idempotency_conflict"
    assert finalized.conflict_class == "idempotency_conflict"
    assert finalized.partial_effect_detected is False

    retry = asyncio.run(repo.begin_attempt(intent=intent, now=now + timedelta(hours=1)))
    assert retry.proceed is True
    assert retry.conflict_class is None
