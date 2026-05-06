"""Lead selection logic for daily memory summary jobs."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping

from src.domain.constants import LEADS_COLLECTION_NAME
from src.adapters.database.firestore.firestore_client_factory import firestore


class MemoryLeadSelector:
    """Selects active leads for batch memory summary processing."""

    def __init__(self, firestore) -> None:
        self.firestore = firestore

    def fetch_active_leads(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[Mapping[str, object]]:
        db = self.firestore
        if firestore is None:  # pragma: no cover
            return []
        leads_ref = db.collection(LEADS_COLLECTION_NAME)
        query = (
            leads_ref.where(filter=firestore.FieldFilter("last_activity_at", ">=", start_utc))
            .where(filter=firestore.FieldFilter("last_activity_at", "<=", end_utc))
        )
        docs = list(query.stream())
        if not docs:
            query = (
                leads_ref.where(filter=firestore.FieldFilter("last_contact_at", ">=", start_utc))
                .where(filter=firestore.FieldFilter("last_contact_at", "<=", end_utc))
            )
            docs = list(query.stream())
        return self.normalize_for_batch(docs)

    @staticmethod
    def normalize_for_batch(docs: list[object]) -> list[Mapping[str, object]]:
        leads: list[Mapping[str, object]] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data.setdefault("lead_id", doc.id)
            leads.append(data)
        return leads
