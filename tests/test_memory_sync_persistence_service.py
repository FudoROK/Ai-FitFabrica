from __future__ import annotations

import asyncio

from src.memory_layer.services.memory_sync_persistence_service import MemorySyncPersistenceService


class _Lead:
    def model_dump(self, *, exclude_none: bool = False):
        assert exclude_none is True
        return {"lead_id": "lead-1", "first_name": "Ann"}


class _Repo:
    def __init__(self, *, rolling_payload):
        self._rolling_payload = rolling_payload

    async def get(self, lead_id):
        assert lead_id == "lead-1"
        return _Lead()

    async def fetch_rolling_summary(self, *, lead_id: str):
        assert lead_id == "lead-1"
        return self._rolling_payload


def test_load_lead_context_treats_non_canonical_rolling_payload_as_empty():
    service = MemorySyncPersistenceService(leads_repo=_Repo(rolling_payload={"lead_id": "lead-1"}))

    context = asyncio.run(service.load_lead_context(lead_id="lead-1"))

    assert context.rolling_summary is None
    assert context.rolling_payload is None


def test_load_lead_context_treats_placeholder_rolling_payload_as_empty():
    service = MemorySyncPersistenceService(
        leads_repo=_Repo(rolling_payload={"rolling_summary_text": "{{ROLLING_SUMMARY}}", "days_count": 1, "version": 1})
    )

    context = asyncio.run(service.load_lead_context(lead_id="lead-1"))

    assert context.rolling_summary is None
    assert context.rolling_payload is None


def test_load_lead_context_normalizes_valid_rolling_summary():
    service = MemorySyncPersistenceService(
        leads_repo=_Repo(
            rolling_payload={
                "rolling_summary_text": "  клиент подтвердил текущий статус  ",
                "days_count": 5,
                "version": 3,
            }
        )
    )

    context = asyncio.run(service.load_lead_context(lead_id="lead-1"))

    assert context.rolling_summary == "клиент подтвердил текущий статус"
    assert context.rolling_payload is not None
    assert context.rolling_payload["rolling_summary_text"] == "  клиент подтвердил текущий статус  "


def test_fetch_confirmed_rolling_summary_validation_detects_expected_version_mismatch():
    service = MemorySyncPersistenceService(
        leads_repo=_Repo(
            rolling_payload={
                "rolling_summary_text": "клиент подтвердил текущий статус",
                "days_count": 5,
                "version": 2,
                "rolling_hash": "hash-v2",
            }
        )
    )

    validation = asyncio.run(
        service.fetch_confirmed_rolling_summary_validation(
            lead_id="lead-1",
            expected_rolling_version=1,
            expected_rolling_hash="hash-v1",
        )
    )

    assert validation.ok is False
    assert validation.reason_code == "rolling_post_commit_version_mismatch"
