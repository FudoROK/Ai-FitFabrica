from __future__ import annotations

from src.adapters.database.sql.health import SqlHealthcheck
from src.adapters.database.sql.models import PortableRuntimeMetadataRow


def test_runtime_metadata_table_name_is_stable() -> None:
    assert PortableRuntimeMetadataRow.__tablename__ == "portable_runtime_metadata"


def test_sql_healthcheck_reports_component_name() -> None:
    health = SqlHealthcheck(engine=None)

    assert health.component_name == "postgresql"
