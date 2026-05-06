from __future__ import annotations

import json


def extract_first_json_object(text: str) -> str:
    fence_json = _extract_from_fenced_block(text)
    if fence_json:
        return fence_json

    stack = 0
    start_idx = -1
    in_string = False
    escape = False
    for idx, ch in enumerate(text):
        if ch == "\\" and in_string:
            escape = not escape
            continue
        if ch == '"' and not escape:
            in_string = not in_string
        if in_string:
            escape = False
            continue
        if ch == "{":
            if stack == 0:
                start_idx = idx
            stack += 1
        elif ch == "}":
            if stack > 0:
                stack -= 1
                if stack == 0 and start_idx >= 0:
                    candidate = text[start_idx : idx + 1]
                    try:
                        parsed = json.loads(candidate)
                    except json.JSONDecodeError:
                        start_idx = -1
                        continue
                    if isinstance(parsed, dict):
                        return candidate
    raise ValueError("json_block_not_found")


def _extract_from_fenced_block(text: str) -> str | None:
    markers = ("```json", "```")
    first = text.find(markers[0])
    if first == -1:
        return None
    start = first + len(markers[0])
    end = text.find(markers[1], start)
    if end == -1:
        return None
    candidate = text[start:end].strip()
    if not candidate:
        return None
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return candidate
    return None
