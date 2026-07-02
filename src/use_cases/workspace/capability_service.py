"""Capability gating for backend-owned workspace features."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.workspace import (
    WORKSPACE_CAPABILITIES,
    WorkspaceBusinessProfileSummary,
    WorkspaceCapabilityMatrixResponse,
    WorkspaceCapabilityState,
    WorkspaceIntegrationSummary,
)
from src.use_cases.workspace.ports import WorkspaceStateRepositoryPort


class WorkspaceCapabilityDeniedError(Exception):
    """Raised when a backend capability is requested before its prerequisites are satisfied."""

    def __init__(self, *, capability: str, reason: str) -> None:
        super().__init__(reason)
        self.capability = capability
        self.reason = reason


@dataclass(frozen=True)
class _WorkspaceCapabilityContext:
    business_profile: WorkspaceBusinessProfileSummary
    integrations: WorkspaceIntegrationSummary


def _resolve_business_profile_summary(profile) -> WorkspaceBusinessProfileSummary:
    if profile is None:
        return WorkspaceBusinessProfileSummary(
            exists=False,
            display_name=None,
            channels=[],
        )
    return WorkspaceBusinessProfileSummary(
        exists=True,
        display_name=profile.display_name,
        channels=list(profile.channels),
    )


def _resolve_integrations_summary(integrations) -> WorkspaceIntegrationSummary:
    return WorkspaceIntegrationSummary(
        has_connected_store=integrations.has_connected_store or bool(integrations.connected_channels),
        connected_channels=list(integrations.connected_channels),
    )


def build_workspace_capability_states(
    *,
    business_profile: WorkspaceBusinessProfileSummary,
    integrations: WorkspaceIntegrationSummary,
) -> list[WorkspaceCapabilityState]:
    """Return one ordered capability matrix derived from persisted workspace state."""
    context = _WorkspaceCapabilityContext(
        business_profile=business_profile,
        integrations=integrations,
    )
    capability_states: list[WorkspaceCapabilityState] = []
    for capability in WORKSPACE_CAPABILITIES:
        capability_states.append(_build_capability_state(capability=capability, context=context))
    return capability_states


def enabled_workspace_capabilities(*, capability_states: list[WorkspaceCapabilityState]) -> list[str]:
    """Return ordered enabled capabilities from a capability matrix."""
    return [item.capability for item in capability_states if item.enabled]


def _build_capability_state(
    *,
    capability: str,
    context: _WorkspaceCapabilityContext,
) -> WorkspaceCapabilityState:
    always_enabled = {
        "try_on_create",
        "outfit_builder_create",
        "similar_search_create",
        "product_card_create",
        "business_profile_manage",
        "manual_export",
    }
    if capability in always_enabled:
        return WorkspaceCapabilityState(capability=capability, enabled=True, disabled_reason=None)

    if capability == "business_templates":
        if context.business_profile.exists:
            return WorkspaceCapabilityState(capability=capability, enabled=True, disabled_reason=None)
        return WorkspaceCapabilityState(
            capability=capability,
            enabled=False,
            disabled_reason="Сначала сохраните business profile, чтобы backend открыл брендовые шаблоны.",
        )

    if capability in {"marketplace_publish", "catalog_import", "catalog_sync"}:
        if context.business_profile.exists and context.integrations.has_connected_store:
            return WorkspaceCapabilityState(capability=capability, enabled=True, disabled_reason=None)
        if context.business_profile.exists:
            return WorkspaceCapabilityState(
                capability=capability,
                enabled=False,
                disabled_reason="Подключите магазин в integrations, чтобы сервер разрешил publish, import и sync.",
            )
        return WorkspaceCapabilityState(
            capability=capability,
            enabled=False,
            disabled_reason="Сначала сохраните business profile и подключите магазин, чтобы backend открыл publish, import и sync.",
        )

    return WorkspaceCapabilityState(
        capability=capability,
        enabled=False,
        disabled_reason="Capability is not enabled for this workspace.",
    )


class WorkspaceCapabilityService:
    """Resolve and enforce backend-owned workspace capability gates."""

    def __init__(self, *, repository: WorkspaceStateRepositoryPort) -> None:
        """Store the repository used to inspect persisted workspace state."""
        self._repository = repository

    async def build_snapshot(self, *, owner_id: str) -> WorkspaceCapabilityMatrixResponse:
        """Return one capability matrix derived from persisted workspace state."""
        profile = await self._repository.get_business_profile(owner_id=owner_id)
        integrations = await self._repository.get_integrations(owner_id=owner_id)
        business_profile_summary = _resolve_business_profile_summary(profile)
        integrations_summary = _resolve_integrations_summary(integrations)
        capability_states = build_workspace_capability_states(
            business_profile=business_profile_summary,
            integrations=integrations_summary,
        )
        return WorkspaceCapabilityMatrixResponse(
            business_profile=business_profile_summary,
            integrations=integrations_summary,
            capability_states=capability_states,
            enabled_capabilities=enabled_workspace_capabilities(capability_states=capability_states),
        )

    async def require_capability(self, *, owner_id: str, capability: str) -> None:
        """Raise a typed error when the requested capability is not enabled."""
        snapshot = await self.build_snapshot(owner_id=owner_id)
        for item in snapshot.capability_states:
            if item.capability != capability:
                continue
            if item.enabled:
                return
            raise WorkspaceCapabilityDeniedError(
                capability=capability,
                reason=item.disabled_reason or "Capability is disabled.",
            )
        raise WorkspaceCapabilityDeniedError(
            capability=capability,
            reason="Unknown workspace capability.",
        )
