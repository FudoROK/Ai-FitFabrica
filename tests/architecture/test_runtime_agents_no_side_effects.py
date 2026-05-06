from __future__ import annotations

import ast
from pathlib import Path


_RUNTIME_AGENT_FILES = list(Path("src/runtime_agents").rglob("*.py"))

_FORBIDDEN_IMPORT_PREFIXES = (
    "requests",
    "httpx",
    "sqlalchemy",
    "src.adapters.database.firestore",
    "src.adapters.crm",
)


def _collect_imports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports


def test_runtime_agents_layer_has_no_side_effect_integrations():
    violations: list[str] = []
    for file_path in _RUNTIME_AGENT_FILES:
        for imported in _collect_imports(file_path):
            if any(imported == prefix or imported.startswith(f"{prefix}.") for prefix in _FORBIDDEN_IMPORT_PREFIXES):
                violations.append(f"{file_path}:{imported}")

    assert violations == []
