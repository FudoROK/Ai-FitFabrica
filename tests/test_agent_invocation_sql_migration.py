from pathlib import Path

from src.adapters.database.sql.agent_invocation_models import AgentInvocationRow


def test_agent_invocation_sql_model_has_a_head_migration() -> None:
    migration = Path("alembic/versions/20260614_000011_agent_invocation_ledger.py").read_text(encoding="utf-8")

    assert 'down_revision = "20260613_000010"' in migration
    assert f'"{AgentInvocationRow.__tablename__}"' in migration
    assert '"input_payload"' not in migration
    assert '"output_payload"' not in migration
    assert '"prompt"' not in migration

