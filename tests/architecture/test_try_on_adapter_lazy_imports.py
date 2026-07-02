from __future__ import annotations

from pathlib import Path


def test_try_on_adapter_package_does_not_eager_import_visual_quality_adapter() -> None:
    source = Path("src/adapters/try_on/__init__.py").read_text(encoding="utf-8")
    top_level_imports = [
        line
        for line in source.splitlines()
        if line.startswith("from .") or line.startswith("import ")
    ]

    assert "from .quality_verifier_agent_adapter import TryOnQualityVerifierAgentAdapter" not in top_level_imports
    assert "TryOnQualityVerifierAgentAdapter" in source
    assert "def __getattr__" in source
