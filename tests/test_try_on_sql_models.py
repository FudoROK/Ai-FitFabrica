from __future__ import annotations

from src.adapters.database.sql.try_on_models import TryOnJobRow, TryOnStoredInputRow


def test_try_on_sql_models_define_job_and_stored_input_tables() -> None:
    assert TryOnJobRow.__tablename__ == "try_on_jobs"
    assert TryOnStoredInputRow.__tablename__ == "try_on_stored_inputs"
