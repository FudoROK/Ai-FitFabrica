from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.workspace_state import WorkspaceOutfitBuilderRequestState
from src.use_cases.workspace.outfit_builder_brief_service import OutfitBuilderBriefService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _RepositoryStub:
    def __init__(self) -> None:
        self._requests: list[WorkspaceOutfitBuilderRequestState] = []

    async def create_outfit_builder_request(self, *, request: WorkspaceOutfitBuilderRequestState, now: datetime) -> WorkspaceOutfitBuilderRequestState:
        stored = request.model_copy(update={"created_at": now, "updated_at": now})
        self._requests.insert(0, stored)
        return stored

    async def list_outfit_builder_requests(self, *, owner_id: str) -> list[WorkspaceOutfitBuilderRequestState]:
        return [request for request in self._requests if request.owner_id == owner_id]


@pytest.mark.asyncio
async def test_outfit_builder_service_persists_request_history() -> None:
    service = OutfitBuilderBriefService(repository=_RepositoryStub(), clock=_utc_now)

    created = await service.create_request(
        occasion="office",
        budget="150",
        base_item="black blazer",
    )
    recent = await service.list_recent_requests()

    assert created["workflow"] == "outfit_builder"
    assert created["status"] == "accepted"
    assert recent[0]["request_id"] == created["request_id"]
    assert recent[0]["occasion"] == "office"


@pytest.mark.asyncio
async def test_outfit_builder_service_returns_completed_status_snapshot() -> None:
    service = OutfitBuilderBriefService(repository=_RepositoryStub(), clock=_utc_now)

    created = await service.create_request(
        occasion="office",
        budget="150",
        base_item="black blazer",
    )
    status = await service.get_request_status(request_id=created["request_id"])

    assert status["request_id"] == created["request_id"]
    assert status["status"] == "completed"
    assert status["status_history"][0]["status"] == "accepted"
    assert status["status_history"][-1]["status"] == "completed"
    assert status["result_summary"]["headline"] == "3 outfit directions prepared"
