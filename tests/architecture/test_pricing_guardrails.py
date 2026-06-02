from __future__ import annotations

from pathlib import Path


def test_pricing_workflow_keeps_recommendation_logic_backend_owned() -> None:
    text = Path("src/use_cases/pricing/workflow_service.py").read_text(encoding="utf-8").lower()
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "window" not in text
    assert "document" not in text
    assert "pricing" in readme
