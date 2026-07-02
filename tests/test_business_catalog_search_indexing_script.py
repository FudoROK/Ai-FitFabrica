from __future__ import annotations

import pytest

from scripts import reindex_business_catalog_search as reindex
from src.use_cases.business_catalog.search_indexing import BusinessCatalogSearchIndexingResult
from src.use_cases.business_catalog.search_indexing_workflow import BusinessCatalogSearchIndexingWorkflow


class _Repository:
    def __init__(self) -> None:
        self.limits: list[int] = []
        self.indexed_product_ids: list[list[str]] = []
        self.failed_product_ids: list[tuple[list[str], str]] = []

    async def list_approved_search_records(self, *, limit: int) -> list[object]:
        self.limits.append(limit)
        return [_Record("product_1"), _Record("product_2")]

    async def list_approved_search_records_by_product_ids(self, *, product_ids: list[str]) -> list[object]:
        return [_Record(product_id) for product_id in product_ids]

    async def mark_search_indexed(self, *, product_ids: list[str]) -> None:
        self.indexed_product_ids.append(product_ids)

    async def mark_search_index_failed(self, *, product_ids: list[str], reason: str) -> None:
        self.failed_product_ids.append((product_ids, reason))


class _Record:
    def __init__(self, product_id: str) -> None:
        self.product_id = product_id


class _IndexingService:
    def __init__(self) -> None:
        self.records: list[object] = []

    async def index_records(self, records: list[object]) -> BusinessCatalogSearchIndexingResult:
        self.records.extend(records)
        return BusinessCatalogSearchIndexingResult(indexed_count=len(records), skipped_count=0)


class _Runtime:
    def __init__(self) -> None:
        self.repository = _Repository()
        self.indexing_service = _IndexingService()
        self.workflow_service = BusinessCatalogSearchIndexingWorkflow(
            repository=self.repository,
            indexing_service=self.indexing_service,
        )


@pytest.mark.asyncio
async def test_reindex_script_indexes_approved_catalog_records(monkeypatch) -> None:
    runtime = _Runtime()

    monkeypatch.setattr(
        reindex,
        "business_catalog_search_indexing_runtime_dependencies",
        lambda settings: runtime,
    )

    result = await reindex.run_reindex(settings=object(), limit=50)

    assert runtime.repository.limits == [50]
    assert len(runtime.indexing_service.records) == 2
    assert runtime.repository.indexed_product_ids == [["product_1", "product_2"]]
    assert runtime.repository.failed_product_ids == []
    assert result == {
        "source_record_count": 2,
        "indexed_count": 2,
        "skipped_count": 0,
    }


@pytest.mark.asyncio
async def test_reindex_script_marks_records_failed_when_indexing_fails(monkeypatch) -> None:
    runtime = _Runtime()

    async def _fail(records: list[object]) -> BusinessCatalogSearchIndexingResult:
        raise RuntimeError("qdrant unavailable")

    runtime.indexing_service.index_records = _fail
    monkeypatch.setattr(
        reindex,
        "business_catalog_search_indexing_runtime_dependencies",
        lambda settings: runtime,
    )

    with pytest.raises(RuntimeError, match="qdrant unavailable"):
        await reindex.run_reindex(settings=object(), limit=50)

    assert runtime.repository.indexed_product_ids == []
    assert runtime.repository.failed_product_ids == [(["product_1", "product_2"], "qdrant unavailable")]


@pytest.mark.asyncio
async def test_search_indexing_workflow_indexes_specific_product_ids() -> None:
    runtime = _Runtime()

    result = await runtime.workflow_service.index_product_ids(product_ids=["product_1"])

    assert result.indexed_count == 1
    assert runtime.repository.indexed_product_ids == [["product_1"]]
