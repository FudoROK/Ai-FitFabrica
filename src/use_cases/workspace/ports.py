"""Ports for persisted workspace state."""

from __future__ import annotations

from typing import Protocol

from src.domain.workspace_state import (
    WorkspaceBusinessProfileState,
    WorkspaceIntegrationState,
    WorkspaceOutfitBuilderRequestState,
)


class WorkspaceStateRepositoryPort(Protocol):
    """Read persisted workspace state for backend-owned bootstrap flows."""

    async def upsert_business_profile(self, *, request, now) -> WorkspaceBusinessProfileState:
        """Persist one business profile for the requested owner."""

    async def upsert_integrations(self, *, request, now) -> WorkspaceIntegrationState:
        """Persist one integrations state for the requested owner."""

    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        """Return the persisted business profile for the requested owner."""

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        """Return the persisted integrations state for the requested owner."""

    async def create_outfit_builder_request(self, *, request, now) -> WorkspaceOutfitBuilderRequestState:
        """Persist one outfit-builder request for the requested owner."""

    async def list_outfit_builder_requests(self, *, owner_id: str) -> list[WorkspaceOutfitBuilderRequestState]:
        """Return persisted outfit-builder requests for the requested owner."""
