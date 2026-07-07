"""Guardrails for async sqlite test engine cleanup."""

from __future__ import annotations

from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parents[1] / "tests"


def test_async_sqlite_tests_dispose_each_created_engine() -> None:
    """Every test-created aiosqlite engine must be disposed before loop teardown."""

    offenders: list[str] = []
    for path in sorted(TEST_ROOT.glob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        if "create_async_engine" not in source or "sqlite+aiosqlite" not in source:
            continue
        created = source.count("create_async_engine(")
        disposed = source.count("engine.dispose(")
        if created != disposed:
            offenders.append(f"{path.relative_to(TEST_ROOT)}: created={created} disposed={disposed}")

    assert offenders == []
