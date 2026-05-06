import ast
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app


def test_http_routes_has_no_main_import_or_main_symbol_usage():
    source = Path("src/entrypoints/http_routes.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("main"):
            raise AssertionError("http_routes.py must not import src.main")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("main"):
                    raise AssertionError("http_routes.py must not import src.main")
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "main":
            raise AssertionError("http_routes.py must not use main.* symbols")


def test_pubsub_runtime_path_does_not_use_main_shims(monkeypatch):
    import src.main as main_module

    client = TestClient(app)

    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr(
        "src.entrypoints.pubsub_routes.dialog_service",
        lambda _settings=None: type("S", (), {"handle_normalized_message": None})(),
    )
    monkeypatch.setattr(main_module, "_dialog_service", lambda: (_ for _ in ()).throw(RuntimeError("must not be called")))

    response = client.post(
        "/pubsub",
        json={
            "message": {
                "data": "eyJjaGFubmVsIjoidGVsZWdyYW0iLCJzb3VyY2VfaWRlbnRpdHkiOiIxIiwiY29udmVyc2F0aW9uX2lkZW50aXR5IjoiMSIsImV2ZW50X2lkZW50aXR5IjoiZXZ0LTEiLCJ0ZXh0IjoiaGkifQ=="
            }
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "pipeline_status": "success"}
