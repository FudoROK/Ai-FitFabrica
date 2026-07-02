"""Qdrant-backed retriever for similarity search."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from src.adapters.vector.qdrant_filters import build_qdrant_filter
from src.adapters.vector.qdrant_index import collection_name_for_vector_namespace
from src.domain.vector_search import VectorPointRecord, VectorSearchHit, VectorSearchQuery


class QdrantVectorRetriever:
    """Persist vector points and execute typed similarity search on Qdrant."""

    def __init__(self, *, client: object, collection_prefix: str) -> None:
        """Bind the shared Qdrant client and naming prefix."""
        self._client = client
        self._collection_prefix = collection_prefix

    def upsert_points(self, *, records: list[VectorPointRecord]) -> None:
        """Write vector points into the namespace-specific collection."""
        if not records:
            return

        namespace = records[0].namespace
        collection_name = collection_name_for_vector_namespace(
            prefix=self._collection_prefix,
            namespace=namespace,
        )
        points = [
            {
                "id": _qdrant_point_id(record),
                "vector": record.embedding,
                "payload": {
                    **record.payload,
                    "owner_id": record.owner_id,
                    "namespace": record.namespace.value,
                    "point_id": record.point_id,
                },
            }
            for record in records
        ]
        self._client.upsert(collection_name=collection_name, points=points)

    def search(self, *, query: VectorSearchQuery) -> list[VectorSearchHit]:
        """Run vector search in the namespace collection and map typed hits."""
        collection_name = collection_name_for_vector_namespace(
            prefix=self._collection_prefix,
            namespace=query.namespace,
        )
        try:
            raw_hits = self._client.search(
                collection_name=collection_name,
                query_vector=query.embedding,
                limit=query.limit,
                query_filter=build_qdrant_filter(query.search_filter),
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_collection_error(exc):
                return []
            raise
        return [
            VectorSearchHit(
                point_id=str(_hit_payload(hit).get("point_id", _hit_id(hit))),
                owner_id=str(_hit_payload(hit)["owner_id"]),
                namespace=query.namespace,
                score=float(_hit_score(hit)),
                payload=dict(_hit_payload(hit)),
            )
            for hit in raw_hits
        ]


def _qdrant_point_id(record: VectorPointRecord) -> str:
    """Map domain point IDs to stable Qdrant-compatible UUID point IDs."""

    return str(uuid5(NAMESPACE_URL, f"{record.namespace.value}:{record.point_id}"))


def _hit_id(hit: object) -> object:
    """Return a Qdrant hit id from dict fakes or real client models."""

    if isinstance(hit, dict):
        return hit["id"]
    return getattr(hit, "id")


def _hit_score(hit: object) -> float:
    """Return a Qdrant hit score from dict fakes or real client models."""

    if isinstance(hit, dict):
        return float(hit["score"])
    return float(getattr(hit, "score"))


def _hit_payload(hit: object) -> dict[str, object]:
    """Return a Qdrant hit payload from dict fakes or real client models."""

    if isinstance(hit, dict):
        return dict(hit["payload"])
    return dict(getattr(hit, "payload") or {})


def _is_missing_collection_error(exc: Exception) -> bool:
    """Return whether Qdrant reports an absent collection for an empty index."""

    content = getattr(exc, "content", b"")
    if isinstance(content, bytes):
        content_text = content.decode("utf-8", errors="ignore")
    else:
        content_text = str(content)
    message = f"{str(exc)} {content_text}".lower()
    status_code = getattr(exc, "status_code", None)
    return (
        ("404" in message or status_code == 404)
        and "collection" in message
        and "exist" in message
    )
