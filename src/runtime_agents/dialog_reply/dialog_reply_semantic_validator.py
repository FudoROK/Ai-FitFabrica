from __future__ import annotations

from .dialog_reply_runtime_schemas import DialogReplyRuntimeOutput


def validate_runtime_semantics(output: DialogReplyRuntimeOutput) -> tuple[bool, str | None]:
    if not output.reply_text.strip():
        return False, "reply_text_empty"
    return True, None
