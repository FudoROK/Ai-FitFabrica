"""Portable SQLAlchemy models for persisted workspace state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class WorkspaceBusinessProfileRow(SqlBase):
    """Persisted business-profile record keyed by workspace owner."""

    __tablename__ = "workspace_business_profiles"

    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    channels_json: Mapped[list[str]] = mapped_column("channels", JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkspaceIntegrationRow(SqlBase):
    """Persisted integrations record keyed by workspace owner."""

    __tablename__ = "workspace_integrations"

    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    connected_channels_json: Mapped[list[str]] = mapped_column("connected_channels", JSON, nullable=False, default=list)
    has_connected_store: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkspaceOutfitBuilderRequestRow(SqlBase):
    """Persisted outfit-builder request record keyed by request identifier."""

    __tablename__ = "workspace_outfit_builder_requests"

    request_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    workflow: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    occasion: Mapped[str] = mapped_column(String(255), nullable=False)
    budget: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_item: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
