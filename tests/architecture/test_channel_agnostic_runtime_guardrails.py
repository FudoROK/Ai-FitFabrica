from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _parse_module(rel_path: str) -> ast.Module:
    return ast.parse(_read(rel_path), filename=rel_path)


def _class_method(module: ast.Module, class_name: str, method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"{class_name}.{method_name} not found")


def _has_call(func: ast.AsyncFunctionDef | ast.FunctionDef, chain: tuple[str, ...]) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue

        target = node.func
        parts: list[str] = []
        while isinstance(target, ast.Attribute):
            parts.append(target.attr)
            target = target.value
        if isinstance(target, ast.Name):
            parts.append(target.id)
            if tuple(reversed(parts)) == chain:
                return True
    return False


def test_dialog_runtime_uses_canonical_channel_identity() -> None:
    gate_module = _parse_module("src/services/inbound/inbound_gate_service.py")
    dialog_module = _parse_module("src/services/dialog/dialog_service.py")
    inbound_use_case_text = _read("src/use_cases/dialog/handle_inbound_message_use_case.py")

    gate_prepare = _class_method(gate_module, "InboundGateService", "prepare")
    assert _has_call(gate_prepare, ("build_channel_identity",))

    dialog_handle_inbound_event = _class_method(dialog_module, "DialogService", "handle_inbound_event")
    assert _has_call(dialog_handle_inbound_event, ("self", "inbound_gate_service", "prepare"))
    assert not _has_call(dialog_handle_inbound_event, ("build_channel_identity",))

    assert "identity = build_channel_identity(message)" in inbound_use_case_text
    for canonical_token in (
        "identity.channel",
        "identity.external_user_id",
        "identity.conversation_identity",
    ):
        assert canonical_token in inbound_use_case_text

    for forbidden_ad_hoc_token in (
        'message.get("channel")',
        'message.get("chat_id")',
        'message.get("external_user_id")',
    ):
        assert forbidden_ad_hoc_token not in inbound_use_case_text
