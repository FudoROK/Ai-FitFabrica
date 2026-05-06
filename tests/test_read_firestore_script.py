from __future__ import annotations

from datetime import datetime, timezone

from scripts.read_firestore import _detect_path_kind, _normalize_firestore_path, _serialize_value


def test_normalize_firestore_path_collapses_extra_slashes() -> None:
    assert _normalize_firestore_path(" /lead_memories//123//daily_summaries/2026-04-20/ ") == "lead_memories/123/daily_summaries/2026-04-20"


def test_detect_path_kind_distinguishes_document_and_collection_paths() -> None:
    assert _detect_path_kind("lead_memories/123") == "document"
    assert _detect_path_kind("lead_memories/123/daily_summaries") == "collection"


def test_serialize_value_normalizes_datetime_and_nested_values() -> None:
    payload = {
        "created_at": datetime(2026, 4, 21, 10, 30, tzinfo=timezone.utc),
        "tags": {"daily", "rolling"},
        "nested": [{"count": 2}],
    }

    serialized = _serialize_value(payload)

    assert serialized["created_at"] == "2026-04-21T10:30:00+00:00"
    assert sorted(serialized["tags"]) == ["daily", "rolling"]
    assert serialized["nested"] == [{"count": 2}]
