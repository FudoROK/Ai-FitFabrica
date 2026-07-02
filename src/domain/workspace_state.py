"""Persisted workspace state used by backend-owned bootstrap flows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBusinessProfileState(BaseModel):
    """Persisted business-profile state owned by the backend."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    channels: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkspaceIntegrationState(BaseModel):
    """Persisted integration state owned by the backend."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    connected_channels: list[str] = Field(default_factory=list)
    has_connected_store: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkspaceOutfitBuilderRequestState(BaseModel):
    """Persisted outfit-builder request owned by the backend."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    workflow: str = Field(min_length=1)
    status: str = Field(min_length=1)
    occasion: str = Field(min_length=1)
    budget: str | None = None
    base_item: str | None = None
    message: str = Field(min_length=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None
