"""Canonical lead identity entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .identity_core_primitives import JsonMap, LeadLifecycleState


@dataclass(slots=True, frozen=True)
class LeadRecord:
    lead_id: UUID
    lifecycle_state: LeadLifecycleState
    display_name: str | None
    metadata: JsonMap
    created_at: datetime
    updated_at: datetime
    suspended_at: datetime | None = None
    merged_into_lead_id: UUID | None = None
