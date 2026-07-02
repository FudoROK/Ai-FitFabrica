from __future__ import annotations

from pathlib import Path


def test_product_card_workflow_stays_backend_owned_and_provider_neutral() -> None:
    text = Path("src/use_cases/product_card/workflow_service.py").read_text(encoding="utf-8").lower()
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "gemini" not in text
    assert "vertex" not in text
    assert "openai" not in text
    assert "anthropic" not in text
    assert "src.adk_agents" not in text
    assert "product-card" in readme


def test_product_card_agent_generation_does_not_reinspect_image_artifacts() -> None:
    text = Path("src/adapters/agents/product_card_generation.py").read_text(encoding="utf-8").lower()

    assert "objectstorage" not in text
    assert "artifact_references=[]" in text
    assert "garment_analysis" in text
