from __future__ import annotations

from types import SimpleNamespace

from scripts import business_catalog_search_index_readiness as readiness


def test_search_index_readiness_migration_check_detects_required_fields() -> None:
    check = readiness._migration_check()

    assert check["status"] == "passed"
    assert check["migration"] == "20260630_000022"


def test_search_index_readiness_runtime_check_detects_worker_handler(monkeypatch) -> None:
    class _WorkerRuntime:
        _handlers = {"business_catalog_search_index": object()}

    monkeypatch.setattr(
        readiness,
        "operations_runtime_dependencies",
        lambda settings: SimpleNamespace(worker_runtime=_WorkerRuntime()),
    )
    monkeypatch.setattr(
        readiness,
        "business_catalog_search_indexing_runtime_dependencies",
        lambda settings: SimpleNamespace(workflow_service=object()),
    )

    checks = readiness._runtime_checks(settings=object())

    assert checks["worker_handler"]["status"] == "passed"
    assert checks["indexing_workflow"]["status"] == "passed"


def test_search_index_readiness_script_is_available_inside_api_image() -> None:
    dockerignore = readiness.PROJECT_ROOT.joinpath(".dockerignore").read_text(encoding="utf-8")

    assert "!scripts/business_catalog_search_index_readiness.py" in dockerignore
