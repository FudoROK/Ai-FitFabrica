"""Reindex approved B2B catalog products into the products vector namespace."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.entrypoints.runtime_dependencies import business_catalog_search_indexing_runtime_dependencies
from src.settings import load_settings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reindex approved B2B catalog products for Similar Search.")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum number of approved catalog records to index.")
    return parser


async def run_reindex(*, settings: object, limit: int) -> dict[str, int]:
    """Load approved catalog records and write them into the vector search index."""

    runtime = business_catalog_search_indexing_runtime_dependencies(settings)
    records = await runtime.repository.list_approved_search_records(limit=limit)
    product_ids = [record.product_id for record in records]
    result = await runtime.workflow_service.index_product_ids(product_ids=product_ids)
    return {
        "source_record_count": len(records),
        "indexed_count": result.indexed_count,
        "skipped_count": result.skipped_count,
    }


async def _async_main() -> int:
    args = _parser().parse_args()
    summary = await run_reindex(settings=load_settings(), limit=args.limit)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def main() -> int:
    """CLI entrypoint."""

    return asyncio.run(_async_main())


if __name__ == "__main__":
    raise SystemExit(main())
