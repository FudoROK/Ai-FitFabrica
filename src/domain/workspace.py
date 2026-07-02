"""Typed domain models for backend-owned workspace bootstrap state."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.domain.billing import BillingOwnerType


class WorkspaceCapability(str):
    """String capability identifier for workspace UI gating."""


WORKSPACE_CAPABILITIES = (
    "try_on_create",
    "outfit_builder_create",
    "similar_search_create",
    "product_card_create",
    "business_profile_manage",
    "business_templates",
    "manual_export",
    "marketplace_publish",
    "catalog_import",
    "catalog_sync",
)


class WorkspaceUserSummary(BaseModel):
    """Minimal user identity shown by the workspace shell."""

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    full_name: str | None = None


class WorkspaceCreditsSummary(BaseModel):
    """Backend-owned credit state used by dashboard cards and forms."""

    model_config = ConfigDict(extra="forbid")

    balance: int = Field(ge=0)
    currency: Literal["credits"] = "credits"
    low_balance_threshold: int | None = Field(default=None, ge=0)
    billing_enabled: bool = False


class WorkspaceWorkflowCosts(BaseModel):
    """Backend-owned workflow costs used for honest frontend gating."""

    model_config = ConfigDict(extra="forbid")

    product_card: int = Field(ge=0)


class WorkspaceBusinessProfileSummary(BaseModel):
    """Business profile activation summary for workspace capability copy."""

    model_config = ConfigDict(extra="forbid")

    exists: bool = False
    display_name: str | None = None
    channels: list[str] = Field(default_factory=list)


class WorkspaceIntegrationSummary(BaseModel):
    """Marketplace/store connection summary for integration-aware actions."""

    model_config = ConfigDict(extra="forbid")

    has_connected_store: bool = False
    connected_channels: list[str] = Field(default_factory=list)


class WorkspaceCapabilityState(BaseModel):
    """One backend-owned capability gate with an explicit enabled/disabled reason."""

    model_config = ConfigDict(extra="forbid")

    capability: str = Field(min_length=1)
    enabled: bool = False
    disabled_reason: str | None = None


class WorkspaceQuickAction(BaseModel):
    """One launch card/CTA exposed by backend-owned workspace state."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    href: str = Field(min_length=1)
    capability: str | None = None
    enabled: bool = True
    disabled_reason: str | None = None


class WorkspaceRecentJobSummary(BaseModel):
    """Compact recent-job row for dashboard and history previews."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(min_length=1)
    href: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    summary: str | None = None


class WorkspaceCreditOwnerSummary(BaseModel):
    """Owner identity used by the frontend to fetch backend-owned balances."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    owner_type: BillingOwnerType


class WorkspaceBootstrapResponse(BaseModel):
    """Unified backend bootstrap payload for the workspace shell."""

    model_config = ConfigDict(extra="forbid")

    user: WorkspaceUserSummary
    credit_owner: WorkspaceCreditOwnerSummary
    credits: WorkspaceCreditsSummary
    workflow_costs: WorkspaceWorkflowCosts
    business_profile: WorkspaceBusinessProfileSummary
    integrations: WorkspaceIntegrationSummary
    capabilities: list[str] = Field(default_factory=list)
    quick_actions: list[WorkspaceQuickAction] = Field(default_factory=list)
    recent_jobs: list[WorkspaceRecentJobSummary] = Field(default_factory=list)


class WorkspaceCapabilityMatrixResponse(BaseModel):
    """Detailed backend-owned capability matrix for server-side gating and diagnostics."""

    model_config = ConfigDict(extra="forbid")

    business_profile: WorkspaceBusinessProfileSummary
    integrations: WorkspaceIntegrationSummary
    capability_states: list[WorkspaceCapabilityState] = Field(default_factory=list)
    enabled_capabilities: list[str] = Field(default_factory=list)
