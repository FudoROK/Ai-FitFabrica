from __future__ import annotations

from .primary_agent_runtime_schemas import MainAgentRuntimeOutput


def validate_runtime_semantics(output: MainAgentRuntimeOutput) -> tuple[bool, str | None]:
    if not output.reply_text.strip():
        return False, "reply_text_empty"
    return True, None
