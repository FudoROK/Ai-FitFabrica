from __future__ import annotations

from pathlib import Path


def test_product_card_workflow_stays_backend_owned_and_provider_neutral() -> None:
    text = Path("src/use_cases/product_card/workflow_service.py").read_text(encoding="utf-8").lower()
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "gemini" not in text
    assert "vertex" not in text
    assert "product-card" in readme
