"""Workflow wrapper for approved business catalog search indexing jobs."""

from __future__ import annotations

from src.use_cases.business_catalog.ports import BusinessCatalogRepositoryPort
from src.use_cases.business_catalog.search_indexing import (
    BusinessCatalogSearchIndexingResult,
    BusinessCatalogSearchIndexingService,
)


class BusinessCatalogSearchIndexingWorkflow:
    """Execute catalog indexing and persist product indexing lifecycle state."""

    def __init__(
        self,
        *,
        repository: BusinessCatalogRepositoryPort,
        indexing_service: BusinessCatalogSearchIndexingService,
    ) -> None:
        """Bind catalog repository and provider-neutral indexing service."""

        self._repository = repository
        self._indexing_service = indexing_service

    async def index_product_ids(self, *, product_ids: list[str]) -> BusinessCatalogSearchIndexingResult:
        """Index approved products by id and mark lifecycle state."""

        if not product_ids:
            return BusinessCatalogSearchIndexingResult(indexed_count=0, skipped_count=0)
        records = await self._repository.list_approved_search_records_by_product_ids(product_ids=product_ids)
        indexed_product_ids = [record.product_id for record in records]
        try:
            result = await self._indexing_service.index_records(records)
        except Exception as exc:
            await self._repository.mark_search_index_failed(product_ids=product_ids, reason=str(exc))
            raise
        if indexed_product_ids:
            await self._repository.mark_search_indexed(product_ids=indexed_product_ids)
        missing_product_ids = [product_id for product_id in product_ids if product_id not in set(indexed_product_ids)]
        if missing_product_ids:
            await self._repository.mark_search_index_failed(
                product_ids=missing_product_ids,
                reason="Product is not approved for search indexing.",
            )
        return result
