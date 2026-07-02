"""Use case for persisted workspace business-profile state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.workspace_state import WorkspaceBusinessProfileState
from src.use_cases.workspace.ports import WorkspaceStateRepositoryPort


class WorkspaceBusinessProfileRequest(BaseModel):
    """Typed request used to persist one workspace business profile."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    channels: list[str] = Field(default_factory=list)


class WorkspaceBusinessProfileService:
    """Persist and read business-profile state through the workspace repository port."""

    def __init__(self, *, repository: WorkspaceStateRepositoryPort, clock) -> None:
        """Store explicit dependencies for business-profile persistence."""
        self._repository = repository
        self._clock = clock

    async def save_business_profile(self, *, request: WorkspaceBusinessProfileRequest) -> WorkspaceBusinessProfileState:
        """Persist one business profile for the requested owner."""
        return await self._repository.upsert_business_profile(request=request, now=self._clock())

    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        """Return the persisted business profile for the requested owner."""
        return await self._repository.get_business_profile(owner_id=owner_id)
