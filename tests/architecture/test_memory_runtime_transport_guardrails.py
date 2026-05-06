from pathlib import Path


_MEMORY_RUNTIME_FILES = [
    Path("src/memory_layer/services/memory_sync_llm_service.py"),
    Path("src/runtime_agents/memory_agent/memory_response_parser.py"),
    Path("src/runtime_agents/memory_agent/memory_daily_runtime_task.py"),
    Path("src/runtime_agents/memory_agent/memory_rolling_runtime_task.py"),
]

_FORBIDDEN_TOKENS = (
    "VertexProvider",
    "_run_memory_agent",
    "invoke_session_flow",
)


def test_memory_runtime_has_no_vertex_or_session_stream_special_path():
    violations: list[str] = []
    for file_path in _MEMORY_RUNTIME_FILES:
        content = file_path.read_text(encoding="utf-8")
        for token in _FORBIDDEN_TOKENS:
            if token in content:
                violations.append(f"{file_path}:{token}")

    assert violations == []
