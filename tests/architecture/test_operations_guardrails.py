from __future__ import annotations

from pathlib import Path


def test_http_route_aggregator_does_not_import_worker_runtime_directly() -> None:
    text = Path("src/entrypoints/http_routes.py").read_text(encoding="utf-8")
    assert "WorkerRuntime" not in text
    assert "WorkflowDispatchService" not in text
