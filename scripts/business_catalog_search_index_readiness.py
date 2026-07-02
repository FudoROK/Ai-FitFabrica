"""Preflight checks for B2B catalog search-index deployment readiness."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.entrypoints.runtime_dependencies import (  # noqa: E402
    business_catalog_search_indexing_runtime_dependencies,
    operations_runtime_dependencies,
    portable_infrastructure,
)
from src.settings import load_settings  # noqa: E402

REQUIRED_MIGRATION = PROJECT_ROOT / "alembic" / "versions" / "20260630_000022_business_catalog_search_index_status.py"
REQUIRED_COLUMNS = {"search_index_status", "search_index_error", "search_indexed_at"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check B2B catalog search-index deployment readiness.")
    parser.add_argument("--require-db", action="store_true", help="Fail if SQL schema cannot be verified.")
    return parser


def _migration_check() -> dict[str, object]:
    """Return whether the search-index migration file contains required fields."""

    if not REQUIRED_MIGRATION.exists():
        return {"status": "failed", "migration": "20260630_000022", "error": "migration_file_missing"}
    source = REQUIRED_MIGRATION.read_text(encoding="utf-8")
    missing = sorted(column for column in REQUIRED_COLUMNS if column not in source)
    if missing:
        return {"status": "failed", "migration": "20260630_000022", "missing_columns": missing}
    return {"status": "passed", "migration": "20260630_000022"}


def _runtime_checks(*, settings: object) -> dict[str, dict[str, object]]:
    """Return checks for runtime wiring without executing indexing work."""

    operations_runtime = operations_runtime_dependencies(settings)
    handlers = getattr(operations_runtime.worker_runtime, "_handlers", {})
    indexing_runtime = business_catalog_search_indexing_runtime_dependencies(settings)
    return {
        "worker_handler": {
            "status": "passed" if "business_catalog_search_index" in handlers else "failed",
            "handler": "business_catalog_search_index",
        },
        "indexing_workflow": {
            "status": "passed" if getattr(indexing_runtime, "workflow_service", None) is not None else "failed",
        },
    }


async def _db_schema_check(*, settings: object, require_db: bool) -> dict[str, object]:
    """Return whether the deployed SQL schema has search-index columns."""

    infrastructure = portable_infrastructure(settings)
    session_factory = getattr(infrastructure, "sql_session_factory", None)
    if session_factory is None:
        return {"status": "failed" if require_db else "skipped", "reason": "sql_not_configured"}
    try:
        async with session_factory() as session:
            rows = (
                await session.execute(
                    text(
                        "select column_name from information_schema.columns "
                        "where table_name = 'business_products'"
                    )
                )
            ).all()
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "reason": str(exc)}
    columns = {str(row[0]) for row in rows}
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        return {"status": "failed", "missing_columns": missing}
    return {"status": "passed", "columns": sorted(REQUIRED_COLUMNS)}


async def run_readiness(*, settings: object, require_db: bool) -> dict[str, object]:
    """Run all readiness checks and return a machine-readable report."""

    checks: dict[str, object] = {
        "migration": _migration_check(),
        **_runtime_checks(settings=settings),
        "db_schema": await _db_schema_check(settings=settings, require_db=require_db),
    }
    failed = [
        name
        for name, result in checks.items()
        if isinstance(result, dict) and result.get("status") == "failed"
    ]
    return {
        "readiness_status": "blocked" if failed else "ready",
        "failed_checks": failed,
        "checks": checks,
    }


async def _async_main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = await run_readiness(settings=load_settings(), require_db=args.require_db)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["readiness_status"] == "ready" else 2


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    return asyncio.run(_async_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
