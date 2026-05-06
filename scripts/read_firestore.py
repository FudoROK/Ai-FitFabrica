#!/usr/bin/env python3
"""Read-only Firestore inspection utility for the local repo environment."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, TypeAlias

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.adapters.database.firestore.firestore_client_factory import get_firestore_client, safe_execute

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
PathKind: TypeAlias = Literal["document", "collection"]


def _normalize_firestore_path(path: str) -> str:
    cleaned = path.strip().strip("/")
    if not cleaned:
        raise ValueError("Firestore path must not be empty")
    parts = [segment.strip() for segment in cleaned.split("/") if segment.strip()]
    if not parts:
        raise ValueError("Firestore path must contain at least one non-empty segment")
    return "/".join(parts)


def _detect_path_kind(path: str) -> PathKind:
    segment_count = len(_normalize_firestore_path(path).split("/"))
    return "document" if segment_count % 2 == 0 else "collection"


def _serialize_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _serialize_value(nested_value) for key, nested_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(item) for item in value]
    return str(value)


def _resolve_reference(client: object, path: str) -> object:
    normalized = _normalize_firestore_path(path)
    segments = normalized.split("/")

    reference = getattr(client, "collection")(segments[0])
    for index, segment in enumerate(segments[1:], start=1):
        step = "document" if index % 2 == 1 else "collection"
        reference = getattr(reference, step)(segment)
    return reference


def _read_document(client: object, path: str) -> dict[str, JsonValue]:
    doc_ref = _resolve_reference(client, path)
    snapshot = safe_execute(getattr(doc_ref, "get"))
    if not getattr(snapshot, "exists", False):
        raise ValueError(f"Document not found: {_normalize_firestore_path(path)}")

    data = getattr(snapshot, "to_dict")()
    payload = data if isinstance(data, dict) else {}
    return {
        "path": _normalize_firestore_path(path),
        "id": str(getattr(snapshot, "id", "")),
        "exists": True,
        "data": _serialize_value(payload),
    }


def _read_collection(client: object, path: str, limit: int) -> dict[str, JsonValue]:
    collection_ref = _resolve_reference(client, path)
    query = getattr(collection_ref, "limit")(limit)
    snapshots = list(safe_execute(getattr(query, "stream")))

    documents: list[JsonValue] = []
    for snapshot in snapshots:
        data = getattr(snapshot, "to_dict")()
        payload = data if isinstance(data, dict) else {}
        documents.append(
            {
                "id": str(getattr(snapshot, "id", "")),
                "path": str(getattr(getattr(snapshot, "reference", object()), "path", "")),
                "data": _serialize_value(payload),
            }
        )

    return {
        "path": _normalize_firestore_path(path),
        "count": len(documents),
        "limit": limit,
        "documents": documents,
    }


def _list_root_collections(client: object) -> dict[str, JsonValue]:
    collections = list(safe_execute(getattr(client, "collections")))
    names = sorted(
        str(getattr(collection_ref, "id", "")).strip()
        for collection_ref in collections
        if str(getattr(collection_ref, "id", "")).strip()
    )
    return {"root_collections": names, "count": len(names)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Firestore inspection utility")
    parser.add_argument(
        "--path",
        help=(
            "Firestore path to inspect. Even segment counts are treated as documents, "
            "odd segment counts as collections."
        ),
    )
    parser.add_argument(
        "--list-root-collections",
        action="store_true",
        help="List root-level collection names",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max documents to stream when --path points to a collection",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.list_root_collections and not args.path:
        parser.error("Provide either --path or --list-root-collections")
    if args.list_root_collections and args.path:
        parser.error("Use --path or --list-root-collections, not both")
    if args.limit < 1:
        parser.error("--limit must be >= 1")

    client = get_firestore_client()
    if not client:
        raise RuntimeError("Firestore client is unavailable")

    if args.list_root_collections:
        result = _list_root_collections(client)
    else:
        assert isinstance(args.path, str)
        kind = _detect_path_kind(args.path)
        result = _read_document(client, args.path) if kind == "document" else _read_collection(client, args.path, args.limit)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
