"""Binding between lead and channel identity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .identity_core_primitives import IdentityBindingState, JsonMap


@dataclass(slots=True, frozen=True)
class IdentityBindingRecord:
    identity_binding_id: UUID
    channel_identity_id: UUID
    lead_id: UUID
    binding_state: IdentityBindingState
    decision_basis: str | None
    provenance: JsonMap
    created_at: datetime
    updated_at: datetime
    revoked_at: datetime | None = None
    superseded_by_binding_id: UUID | None = None
