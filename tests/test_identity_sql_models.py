from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.adapters.database.sql.identity_models import ChannelIdentityRow, IdentityBindingRow, PersonRow
from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, LeadLifecycleState
from src.identity_core.models.lead import LeadRecord


def test_lead_record_exposes_person_id_field() -> None:
    lead = LeadRecord(
        lead_id=uuid4(),
        person_id=uuid4(),
        lifecycle_state=LeadLifecycleState.ACTIVE,
        display_name=None,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert lead.person_id is not None


def test_identity_table_names_are_stable() -> None:
    assert PersonRow.__tablename__ == "persons"
    assert ChannelIdentityRow.__tablename__ == "channel_identities"
    assert IdentityBindingRow.__tablename__ == "identity_bindings"


def test_channel_identity_record_exposes_person_id_field() -> None:
    channel_identity = ChannelIdentityRecord(
        channel_identity_id=uuid4(),
        person_id=uuid4(),
        channel="telegram",
        external_identity="42",
        lifecycle_state=ChannelIdentityState.ACTIVE,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert channel_identity.person_id is not None
