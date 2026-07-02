from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
TESTS_ROOT = REPO_ROOT / "tests"
LEGACY_FACADE_MODULE = "src.firestore_client"


def _file_to_module(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).with_suffix("")
    return ".".join(rel.parts)


def _resolve_imported_module(module: str | None, node: ast.ImportFrom, file_module: str) -> str:
    if node.level == 0:
        return module or ""

    parts = file_module.split(".")
    keep = max(0, len(parts) - node.level)
    base = parts[:keep]
    if module:
        base.extend(module.split("."))
    return ".".join(base)


def _collect_imports(path: Path) -> list[str]:
    file_module = _file_to_module(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(_resolve_imported_module(node.module, node, file_module))
    return imports


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def test_runtime_source_has_no_removed_firestore_facade_imports() -> None:
    violations: list[str] = []
    for path in _iter_python_files(SRC_ROOT):
        if path.relative_to(REPO_ROOT).as_posix() == "src/firestore_client.py":
            continue
        for imported in _collect_imports(path):
            if imported.startswith(LEGACY_FACADE_MODULE):
                rel = path.relative_to(REPO_ROOT).as_posix()
                violations.append(f"{rel} imports removed facade module '{imported}'")

    assert not violations, "\n".join(violations)


def test_architecture_tests_do_not_depend_on_removed_firestore_facade_file() -> None:
    forbidden_tokens = (
        "Path(\"src/firestore_client.py\")",
        "Path('src/firestore_client.py')",
        "src/firestore_client.py",
    )
    allowed_file = "tests/architecture/test_firestore_client_infra_guardrail.py"

    violations: list[str] = []
    for path in _iter_python_files(TESTS_ROOT / "architecture"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == allowed_file:
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                violations.append(f"{rel} contains forbidden removed facade file token: {token}")

    assert not violations, "\n".join(violations)


def test_runtime_lazy_factories_do_not_expose_removed_firestore_session_factory() -> None:
    text = (SRC_ROOT / "entrypoints" / "runtime_dependency_lazy_factories.py").read_text(encoding="utf-8")
    assert "def FirestoreSessionRepository" not in text
