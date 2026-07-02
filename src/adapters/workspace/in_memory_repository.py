"""In-memory workspace-state repository used when SQL is unavailable."""

from __future__ import annotations

from src.domain.workspace_state import (
    WorkspaceBusinessProfileState,
    WorkspaceIntegrationState,
    WorkspaceOutfitBuilderRequestState,
)


class InMemoryWorkspaceStateRepository:
    """Store workspace state in memory for tests and local fallbacks."""

    def __init__(
        self,
        *,
        business_profiles: list[WorkspaceBusinessProfileState] | None = None,
        integrations: list[WorkspaceIntegrationState] | None = None,
        outfit_builder_requests: list[WorkspaceOutfitBuilderRequestState] | None = None,
    ) -> None:
        """Seed optional in-memory workspace state."""
        self._business_profiles = {profile.owner_id: profile for profile in (business_profiles or [])}
        self._integrations = {integration.owner_id: integration for integration in (integrations or [])}
        self._outfit_builder_requests: dict[str, list[WorkspaceOutfitBuilderRequestState]] = {}
        for request in outfit_builder_requests or []:
            self._outfit_builder_requests.setdefault(request.owner_id, []).append(request)

    async def upsert_business_profile(self, *, request, now) -> WorkspaceBusinessProfileState:
        """Persist one business profile in memory."""
        existing = self._business_profiles.get(request.owner_id)
        profile = WorkspaceBusinessProfileState(
            owner_id=request.owner_id,
            display_name=request.display_name,
            channels=list(request.channels),
            created_at=now if existing is None else existing.created_at,
            updated_at=now,
        )
        self._business_profiles[request.owner_id] = profile
        return profile

    async def upsert_integrations(self, *, request, now) -> WorkspaceIntegrationState:
        """Persist one integrations state in memory."""
        existing = self._integrations.get(request.owner_id)
        integrations = WorkspaceIntegrationState(
            owner_id=request.owner_id,
            connected_channels=list(request.connected_channels),
            has_connected_store=request.has_connected_store,
            created_at=now if existing is None else existing.created_at,
            updated_at=now,
        )
        self._integrations[request.owner_id] = integrations
        return integrations

    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        """Return the stored business profile for the requested owner."""
        return self._business_profiles.get(owner_id)

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        """Return the stored integrations state for the requested owner."""
        return self._integrations.get(
            owner_id,
            WorkspaceIntegrationState(
                owner_id=owner_id,
                connected_channels=[],
                has_connected_store=False,
            ),
        )

    async def create_outfit_builder_request(self, *, request, now) -> WorkspaceOutfitBuilderRequestState:
        """Persist one outfit-builder request in memory."""
        stored = WorkspaceOutfitBuilderRequestState(
            owner_id=request.owner_id,
            request_id=request.request_id,
            workflow=request.workflow,
            status=request.status,
            occasion=request.occasion,
            budget=request.budget,
            base_item=request.base_item,
            message=request.message,
            created_at=now,
            updated_at=now,
        )
        requests = self._outfit_builder_requests.setdefault(request.owner_id, [])
        requests.insert(0, stored)
        return stored

    async def list_outfit_builder_requests(self, *, owner_id: str) -> list[WorkspaceOutfitBuilderRequestState]:
        """Return stored outfit-builder requests for the requested owner."""
        return list(self._outfit_builder_requests.get(owner_id, []))
