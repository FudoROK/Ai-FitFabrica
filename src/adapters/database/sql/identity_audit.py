"""Audit primitives for canonical identity resolution events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from .identity_models import IdentityResolutionAuditRow


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class IdentityResolutionAuditEntry:
    """Serializable audit payload for one identity resolution decision."""

    lead_id: UUID | None
    person_id: UUID | None
    channel_identity_id: UUID | None
    decision_mode: str
    external_identity_hash: str
    binding_created: bool
    person_created: bool
    lead_created: bool
    metadata: dict[str, object]
    created_at: datetime


class IdentityResolutionResultLike(Protocol):
    """Minimal resolution result shape required for audit entry construction."""

    channel: str
    binding_created: bool
    person_created: bool
    lead_created: bool


def build_identity_resolution_audit_entry(
    *,
    result: IdentityResolutionResultLike,
    external_identity_hash: str,
    lead_id: UUID | None,
    person_id: UUID | None,
    channel_identity_id: UUID | None,
    decision_mode: str,
) -> IdentityResolutionAuditEntry:
    """Build a normalized audit entry from the runtime resolution result."""
    return IdentityResolutionAuditEntry(
        lead_id=lead_id,
        person_id=person_id,
        channel_identity_id=channel_identity_id,
        decision_mode=decision_mode,
        external_identity_hash=external_identity_hash,
        binding_created=result.binding_created,
        person_created=result.person_created,
        lead_created=result.lead_created,
        metadata={"channel": result.channel},
        created_at=_utc_now(),
    )


class SqlIdentityResolutionAuditRecorder:
    """Persist identity resolution audit entries through SQLAlchemy sessions."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared session factory."""
        self._session_factory = session_factory

    async def record(self, *, entry: IdentityResolutionAuditEntry) -> None:
        """Insert one audit row for the given resolution entry."""
        async with self._session_factory() as session:
            session.add(
                IdentityResolutionAuditRow(
                    identity_resolution_audit_id=uuid4(),
                    person_id=entry.person_id,
                    lead_id=entry.lead_id,
                    channel_identity_id=entry.channel_identity_id,
                    decision_mode=entry.decision_mode,
                    external_identity_hash=entry.external_identity_hash,
                    binding_created=entry.binding_created,
                    person_created=entry.person_created,
                    lead_created=entry.lead_created,
                    metadata_json=dict(entry.metadata),
                    created_at=entry.created_at,
                )
            )
            await session.commit()
