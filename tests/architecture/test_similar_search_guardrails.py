from __future__ import annotations

from pathlib import Path


def test_similar_search_stays_backend_owned_and_vendor_neutral() -> None:
    text = Path("src/use_cases/similar_search/workflow_service.py").read_text(encoding="utf-8").lower()
    assert "vertex ai search" not in text
    assert "discoveryengine" not in text
