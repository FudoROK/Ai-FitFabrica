import ast
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import build_app
from src.settings import Settings


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

def test_web_first_runtime_excludes_removed_ingress_routes() -> None:
    client = TestClient(
        build_app(
            Settings(
                ENVIRONMENT="test",
                GCP_PROJECT_ID="fitfabrica-test",
                PUBSUB_TOPIC_NAME="fitfabrica-events",
                LLM_PROVIDER="fake",
                MEMORY_SUMMARY_ENABLED=False,
                MESSAGING_PROVIDER="none",
            )
        )
    )

    assert client.post("/webhook/telegram", json={}).status_code == 404
    assert client.post("/pubsub", json={}).status_code == 404
    assert client.post("/tasks/memory-summary", json={}).status_code == 404


def test_main_and_runtime_dependencies_do_not_expose_removed_dialog_runtime_shims() -> None:
    main_source = Path("src/main.py").read_text(encoding="utf-8")
    runtime_source = Path("src/entrypoints/runtime_dependencies.py").read_text(encoding="utf-8")
    http_routes_source = Path("src/entrypoints/http_routes.py").read_text(encoding="utf-8")

    assert "def _dialog_service" not in main_source
    assert "def dialog_service(" not in runtime_source
    assert "def ingress_rate_limiter(" not in runtime_source
    assert "def ingress_global_safety_limiter(" not in runtime_source
    assert "def memory_summary_service(" not in runtime_source
    assert "def safe_memory_summary_response(" not in runtime_source
    assert "internal_task_routes" not in http_routes_source
