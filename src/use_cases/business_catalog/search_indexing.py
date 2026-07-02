"""Index approved business catalog products into Similar Search."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.provider_models import EmbeddingRequest
from src.domain.vector_search import VectorNamespace, VectorPointRecord
from src.use_cases.business_catalog.ports import (
    BusinessCatalogVectorBootstrapperPort,
    BusinessCatalogVectorIndexPort,
)
from src.use_cases.business_catalog.search_projection import BusinessCatalogSearchRecord
from src.use_cases.similar_search.ports import SimilarSearchEmbeddingPort


class BusinessCatalogSearchIndexingResult(BaseModel):
    """Summary returned after indexing approved business catalog records."""

    model_config = ConfigDict(extra="forbid")

    indexed_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)


class BusinessCatalogSearchIndexingService:
    """Convert approved catalog search records into product vector points."""

    def __init__(
        self,
        *,
        embedding_provider: SimilarSearchEmbeddingPort,
        vector_index: BusinessCatalogVectorIndexPort,
        vector_bootstrapper: BusinessCatalogVectorBootstrapperPort | None = None,
    ) -> None:
        """Store provider-neutral indexing dependencies."""

        self._embedding_provider = embedding_provider
        self._vector_index = vector_index
        self._vector_bootstrapper = vector_bootstrapper

    async def index_records(
        self,
        records: list[BusinessCatalogSearchRecord],
    ) -> BusinessCatalogSearchIndexingResult:
        """Index approved records into the product vector namespace."""

        vector_records: list[VectorPointRecord] = []
        skipped_count = 0
        for record in records:
            embedding_input = build_catalog_embedding_input(record)
            if not embedding_input.strip():
                skipped_count += 1
                continue
            embedding = self._embedding_provider.embed(
                EmbeddingRequest(
                    namespace=VectorNamespace.PRODUCTS.value,
                    input_text=embedding_input,
                )
            )
            vector_records.append(
                VectorPointRecord(
                    point_id=f"business-catalog:{record.product_id}",
                    namespace=VectorNamespace.PRODUCTS,
                    embedding=embedding.embedding,
                    owner_id=record.product_id,
                    payload={
                        "product_id": record.product_id,
                        "merchant_id": record.merchant_id,
                        "category": record.category,
                        "city": record.city,
                        "country_code": record.country_code.upper(),
                        "currency": record.currency.upper(),
                        "price_amount": float(record.price_amount),
                        "marketplace_source_type": record.marketplace_source_type,
                        "source_trust_score": record.source_trust_score,
                    },
                )
            )
        if vector_records and self._vector_bootstrapper is not None:
            self._vector_bootstrapper.ensure_collection(namespace=VectorNamespace.PRODUCTS)
        self._vector_index.upsert_points(records=vector_records)
        return BusinessCatalogSearchIndexingResult(indexed_count=len(vector_records), skipped_count=skipped_count)


def build_catalog_embedding_input(record: BusinessCatalogSearchRecord) -> str:
    """Build stable embedding text from search-safe catalog fields."""

    parts = [
        f"title: {record.title}",
        f"category: {record.category}",
        f"description: {record.description or ''}",
        f"location: {record.city}, {record.country_code.upper()}",
        f"delivery: {', '.join(record.delivery_regions)}",
        f"price: {record.price_amount} {record.currency.upper()}",
        f"source: {record.marketplace_source_type}",
    ]
    return "; ".join(part for part in parts if part.strip())
