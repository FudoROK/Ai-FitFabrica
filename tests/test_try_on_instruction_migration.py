from pathlib import Path


def test_try_on_instruction_migration_is_chained_after_analysis_bundle() -> None:
    text = Path("alembic/versions/20260615_000016_try_on_instruction.py").read_text(encoding="utf-8")

    assert 'revision = "20260615_000016"' in text
    assert 'down_revision = "20260615_000015"' in text
    assert '"try_on_instructions"' in text
