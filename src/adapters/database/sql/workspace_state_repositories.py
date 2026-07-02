"""SQL-backed repositories for persisted workspace state."""

from __future__ import annotations

from sqlalchemy import desc, select

from src.domain.workspace_state import (
    WorkspaceBusinessProfileState,
    WorkspaceIntegrationState,
    WorkspaceOutfitBuilderRequestState,
)

from .workspace_state_models import WorkspaceBusinessProfileRow, WorkspaceIntegrationRow, WorkspaceOutfitBuilderRequestRow


class SqlWorkspaceStateRepository:
    """Read workspace state from portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def upsert_business_profile(self, *, request, now) -> WorkspaceBusinessProfileState:
        """Persist one business profile for the requested owner."""
        async with self._session_factory() as session:
            row = await session.get(WorkspaceBusinessProfileRow, request.owner_id)
            if row is None:
                row = WorkspaceBusinessProfileRow(
                    owner_id=request.owner_id,
                    display_name=request.display_name,
                    channels_json=list(request.channels),
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.display_name = request.display_name
                row.channels_json = list(request.channels)
                row.updated_at = now
            await session.commit()
            return WorkspaceBusinessProfileState(
                owner_id=row.owner_id,
                display_name=row.display_name,
                channels=list(row.channels_json),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def upsert_integrations(self, *, request, now) -> WorkspaceIntegrationState:
        """Persist one integrations state for the requested owner."""
        async with self._session_factory() as session:
            row = await session.get(WorkspaceIntegrationRow, request.owner_id)
            if row is None:
                row = WorkspaceIntegrationRow(
                    owner_id=request.owner_id,
                    connected_channels_json=list(request.connected_channels),
                    has_connected_store=request.has_connected_store,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.connected_channels_json = list(request.connected_channels)
                row.has_connected_store = request.has_connected_store
                row.updated_at = now
            await session.commit()
            return WorkspaceIntegrationState(
                owner_id=row.owner_id,
                connected_channels=list(row.connected_channels_json),
                has_connected_store=bool(row.has_connected_store),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        """Return the persisted business profile for the requested owner."""
        async with self._session_factory() as session:
            row = await session.get(WorkspaceBusinessProfileRow, owner_id)
            if row is None:
                return None
            return WorkspaceBusinessProfileState(
                owner_id=row.owner_id,
                display_name=row.display_name,
                channels=list(row.channels_json),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        """Return the persisted integrations state for the requested owner."""
        async with self._session_factory() as session:
            row = await session.get(WorkspaceIntegrationRow, owner_id)
            if row is None:
                return WorkspaceIntegrationState(
                    owner_id=owner_id,
                    connected_channels=[],
                    has_connected_store=False,
                )
            return WorkspaceIntegrationState(
                owner_id=row.owner_id,
                connected_channels=list(row.connected_channels_json),
                has_connected_store=bool(row.has_connected_store),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def create_outfit_builder_request(self, *, request, now) -> WorkspaceOutfitBuilderRequestState:
        """Persist one outfit-builder request for the requested owner."""
        async with self._session_factory() as session:
            row = WorkspaceOutfitBuilderRequestRow(
                request_id=request.request_id,
                owner_id=request.owner_id,
                workflow=request.workflow,
                status=request.status,
                occasion=request.occasion,
                budget=request.budget,
                base_item=request.base_item,
                message=request.message,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            await session.commit()
            return WorkspaceOutfitBuilderRequestState(
                owner_id=row.owner_id,
                request_id=row.request_id,
                workflow=row.workflow,
                status=row.status,
                occasion=row.occasion,
                budget=row.budget,
                base_item=row.base_item,
                message=row.message,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def list_outfit_builder_requests(self, *, owner_id: str) -> list[WorkspaceOutfitBuilderRequestState]:
        """Return persisted outfit-builder requests for the requested owner."""
        async with self._session_factory() as session:
            statement = (
                select(WorkspaceOutfitBuilderRequestRow)
                .where(WorkspaceOutfitBuilderRequestRow.owner_id == owner_id)
                .order_by(desc(WorkspaceOutfitBuilderRequestRow.created_at))
            )
            rows = (await session.execute(statement)).scalars().all()
            return [
                WorkspaceOutfitBuilderRequestState(
                    owner_id=row.owner_id,
                    request_id=row.request_id,
                    workflow=row.workflow,
                    status=row.status,
                    occasion=row.occasion,
                    budget=row.budget,
                    base_item=row.base_item,
                    message=row.message,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in rows
            ]
