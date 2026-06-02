"""Qdrant-backed retriever for similarity search."""

from __future__ import annotations

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
                "id": record.point_id,
                "vector": record.embedding,
                "payload": {
                    **record.payload,
                    "owner_id": record.owner_id,
                    "namespace": record.namespace.value,
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
        raw_hits = self._client.search(
            collection_name=collection_name,
            query_vector=query.embedding,
            limit=query.limit,
            query_filter=build_qdrant_filter(query.search_filter),
        )
        return [
            VectorSearchHit(
                point_id=str(hit["id"]),
                owner_id=str(hit["payload"]["owner_id"]),
                namespace=query.namespace,
                score=float(hit["score"]),
                payload=dict(hit["payload"]),
            )
            for hit in raw_hits
        ]
