from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "src" / "llm" / "tasks"
SERVICES_DIR = ROOT / "src" / "services"


BANNED_SNIPPETS = [
    "output_text",
    "tool_calls",
    "client.responses",
    "responses.create",
    "previous_response_id",
    "vector_store_ids",
]


def _iter_py_files(base: Path):
    for path in base.rglob("*.py"):
        yield path


def test_tasks_and_services_do_not_import_openai():
    targets = list(_iter_py_files(TASKS_DIR)) + list(_iter_py_files(SERVICES_DIR))
    offenders: list[str] = []
    for path in targets:
        text = path.read_text(encoding="utf-8")
        if "import openai" in text or "from openai" in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, f"OpenAI import leakage detected: {offenders}"


def test_tasks_and_services_do_not_reference_openai_envelope_fields():
    targets = list(_iter_py_files(TASKS_DIR)) + list(_iter_py_files(SERVICES_DIR))
    offenders: list[str] = []
    for path in targets:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for snippet in BANNED_SNIPPETS:
            if snippet in text:
                offenders.append(f"{rel}:{snippet}")
    assert not offenders, f"OpenAI envelope leakage detected: {offenders}"


def test_openai_provider_module_deleted():
    assert not (ROOT / "src" / "llm" / "providers" / "openai_provider.py").exists()


def test_core_request_contract_has_no_openai_only_fields():
    text = (ROOT / "src" / "llm" / "core" / "request.py").read_text(encoding="utf-8")
    assert "vector_store_ids" not in text
    assert "previous_response_id" not in text


def test_vertex_provider_is_implemented():
    text = (ROOT / "src" / "llm" / "vertex" / "vertex_provider.py").read_text(encoding="utf-8")
    assert "NotImplementedError" not in text
