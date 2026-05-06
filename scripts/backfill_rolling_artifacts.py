#!/usr/bin/env python3
"""Backfill legacy rolling_summaries/current into rolling_artifacts + rolling_current pointer."""
from __future__ import annotations

import argparse
import logging
from hashlib import sha256
from datetime import datetime, timezone

from src.domain.memory.rolling_content_policy import validate as validate_rolling_content
from src.adapters.database.firestore.firestore_client_factory import get_firestore_client, safe_execute
from src.adapters.database.firestore.summary_store import (
    build_rolling_artifact_id,
    create_rolling_artifact,
    promote_rolling_pointer,
)

logger = logging.getLogger(__name__)


def _iter_lead_ids(limit: int | None) -> list[str]:
    client = get_firestore_client()
    if not client:
        return []
    docs = safe_execute(client.collection("lead_memories").stream)
    lead_ids: list[str] = []
    for doc in docs:
        lead_id = getattr(doc, "id", None)
        if isinstance(lead_id, str) and lead_id.strip():
            lead_ids.append(lead_id.strip())
        if limit is not None and len(lead_ids) >= limit:
            break
    return lead_ids


def _build_hash_from_text(text: str) -> str:
    return sha256(text.strip().encode("utf-8")).hexdigest()


def _backfill_lead(*, lead_id: str, updated_at: datetime) -> bool:
    client = get_firestore_client()
    if not client:
        logger.warning("backfill_skipped_firestore_unavailable", extra={"lead_id": lead_id})
        return False
    legacy_ref = (
        client.collection("lead_memories")
        .document(lead_id)
        .collection("rolling_summaries")
        .document("current")
    )
    snapshot = safe_execute(legacy_ref.get)
    if not snapshot or not getattr(snapshot, "exists", False):
        return False
    payload = snapshot.to_dict() or {}
    summary_text = payload.get("rolling_summary_text")
    if not isinstance(summary_text, str):
        return False
    validated = validate_rolling_content(summary_text)
    if not validated.ok:
        return False
    normalized_text = validated.normalized_text or summary_text.strip()
    rolling_payload = dict(payload)
    rolling_payload["rolling_summary_text"] = normalized_text
    rolling_payload["updated_at"] = updated_at
    rolling_payload.setdefault("created_at", payload.get("created_at") or updated_at)
    rolling_payload["rolling_hash"] = str(payload.get("rolling_hash") or "").strip() or _build_hash_from_text(normalized_text)

    artifact_id = build_rolling_artifact_id(lead_id=lead_id, rolling_payload=rolling_payload)
    if not artifact_id:
        return False
    artifact_created = create_rolling_artifact(
        lead_id=lead_id,
        artifact_id=artifact_id,
        artifact_payload=rolling_payload,
    )
    pointer_promoted = promote_rolling_pointer(
        lead_id=lead_id,
        artifact_id=artifact_id,
        pointer_payload={
            "updated_at": updated_at,
            "version": rolling_payload.get("version"),
            "rolling_hash": rolling_payload.get("rolling_hash"),
        },
    )
    return bool(artifact_created and pointer_promoted)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill rolling artifacts/pointers from legacy current docs")
    parser.add_argument("--lead-id", action="append", help="Specific lead id to backfill (repeatable)")
    parser.add_argument("--limit", type=int, default=None, help="Max number of leads when scanning all")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    lead_ids = [str(item).strip() for item in (args.lead_id or []) if str(item).strip()]
    if not lead_ids:
        lead_ids = _iter_lead_ids(limit=args.limit)

    updated_at = datetime.now(tz=timezone.utc)
    success = 0
    skipped = 0
    for lead_id in lead_ids:
        ok = _backfill_lead(lead_id=lead_id, updated_at=updated_at)
        if ok:
            success += 1
        else:
            skipped += 1

    logger.info("backfill_rolling_artifacts_finished", extra={"total": len(lead_ids), "success": success, "skipped": skipped})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
