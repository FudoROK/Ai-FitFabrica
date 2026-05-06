from __future__ import annotations

from pathlib import Path

NEUTRAL_FILES = [
    Path("src/llm/vertex/vertex_provider.py"),
    Path("src/llm/vertex/vertex_invocation.py"),
    Path("src/llm/transport/structured_extractor.py"),
]

FORBIDDEN_IMPORT_MARKERS = [
    "AgentOutput",
    "MemoryAgentOutput",
    "validate_agent_output",
]

FORBIDDEN_DOMAIN_FIELD_MARKERS = [
    '"reply_text"',
    '"system_payload"',
]


def test_transport_core_has_no_domain_output_contract_imports() -> None:
    for file_path in NEUTRAL_FILES:
        source = file_path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_IMPORT_MARKERS:
            assert marker not in source, f"{marker} must not be used in {file_path}"


def test_transport_core_has_no_reply_specific_field_assumptions() -> None:
    for file_path in NEUTRAL_FILES:
        source = file_path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_DOMAIN_FIELD_MARKERS:
            assert marker not in source, f"{marker} must not be hardcoded in {file_path}"
