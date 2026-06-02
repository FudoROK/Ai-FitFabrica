from __future__ import annotations

from pathlib import Path


def test_business_runtime_layers_do_not_construct_vertex_or_gemini_providers_directly() -> None:
    for relative_path in [
        "src/llm/llm_service.py",
        "src/entrypoints/runtime_dependencies.py",
    ]:
        text = Path(relative_path).read_text(encoding="utf-8")
        assert "GeminiStructuredProvider(" not in text
        assert "VertexProvider(" not in text
