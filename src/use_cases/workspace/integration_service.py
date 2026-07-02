"""Use case for persisted workspace integrations state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.workspace_state import WorkspaceIntegrationState
from src.use_cases.workspace.ports import WorkspaceStateRepositoryPort


class WorkspaceIntegrationRequest(BaseModel):
    """Typed request used to persist one workspace integrations state."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    connected_channels: list[str] = Field(default_factory=list)
    has_connected_store: bool = False


class WorkspaceIntegrationService:
    """Persist and read integrations state through the workspace repository port."""

    def __init__(self, *, repository: WorkspaceStateRepositoryPort, clock) -> None:
        """Store explicit dependencies for integrations persistence."""
        self._repository = repository
        self._clock = clock

    async def save_integrations(self, *, request: WorkspaceIntegrationRequest) -> WorkspaceIntegrationState:
        """Persist integrations state for the requested owner."""
        return await self._repository.upsert_integrations(request=request, now=self._clock())

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        """Return the persisted integrations state for the requested owner."""
        return await self._repository.get_integrations(owner_id=owner_id)
