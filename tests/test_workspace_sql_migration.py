from pathlib import Path

from src.adapters.database.sql.workspace_state_models import (
    WorkspaceBusinessProfileRow,
    WorkspaceIntegrationRow,
    WorkspaceOutfitBuilderRequestRow,
)


def test_workspace_sql_models_have_a_head_migration() -> None:
    migration = Path("alembic/versions/20260613_000010_workspace_state.py").read_text(encoding="utf-8")

    assert 'down_revision = "20260531_000009"' in migration
    for model in (
        WorkspaceBusinessProfileRow,
        WorkspaceIntegrationRow,
        WorkspaceOutfitBuilderRequestRow,
    ):
        assert f'"{model.__tablename__}"' in migration
