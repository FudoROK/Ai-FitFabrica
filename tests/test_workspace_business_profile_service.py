from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.workspace_state import WorkspaceBusinessProfileState
from src.use_cases.workspace.business_profile_service import WorkspaceBusinessProfileRequest, WorkspaceBusinessProfileService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _RepositoryStub:
    async def upsert_business_profile(self, *, request: WorkspaceBusinessProfileRequest, now: datetime) -> WorkspaceBusinessProfileState:
        return WorkspaceBusinessProfileState(
            owner_id=request.owner_id,
            display_name=request.display_name,
            channels=list(request.channels),
            created_at=now,
            updated_at=now,
        )

    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        return WorkspaceBusinessProfileState(
            owner_id=owner_id,
            display_name="FitFabrica Studio",
            channels=["instagram", "wildberries"],
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )


@pytest.mark.asyncio
async def test_workspace_business_profile_service_saves_profile() -> None:
    service = WorkspaceBusinessProfileService(repository=_RepositoryStub(), clock=_utc_now)

    result = await service.save_business_profile(
        request=WorkspaceBusinessProfileRequest(
            owner_id="public-person",
            display_name="FitFabrica Studio",
            channels=["instagram", "wildberries"],
        )
    )

    assert result.owner_id == "public-person"
    assert result.display_name == "FitFabrica Studio"
    assert result.channels == ["instagram", "wildberries"]


@pytest.mark.asyncio
async def test_workspace_business_profile_service_reads_profile() -> None:
    service = WorkspaceBusinessProfileService(repository=_RepositoryStub(), clock=_utc_now)

    result = await service.get_business_profile(owner_id="public-person")

    assert result is not None
    assert result.display_name == "FitFabrica Studio"
