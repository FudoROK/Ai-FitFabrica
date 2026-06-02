from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps


def test_runtime_identity_repositories_prefer_sql_when_portable_infrastructure_exists(monkeypatch) -> None:
    settings = SimpleNamespace()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory"),
    )

    repositories = deps.identity_runtime_repositories(settings)

    assert repositories.channel_identity_repo.__class__.__name__.startswith("Sql")
