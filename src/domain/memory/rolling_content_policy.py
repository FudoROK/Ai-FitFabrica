from __future__ import annotations

from dataclasses import dataclass
import re

_PLACEHOLDER_EXACT_MATCHES = frozenset(
    {
        "n/a",
        "na",
        "none",
        "null",
        "todo",
        "tbd",
        "placeholder",
        "rolling summary",
        "summary",
        "-",
        "...",
    }
)
_PLACEHOLDER_TOKEN_PATTERN = re.compile(
    r"(\{\{[^}]+\}\}|\[\[[^\]]+\]\]|<[^>]+>|fill\s+in|insert\s+here|template|placeholder)",
    re.IGNORECASE,
)
_SEMANTIC_NOISE_PATTERN = re.compile(r"(asdf|qwerty|lorem ipsum|test test|blah blah)", re.IGNORECASE)
_REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{7,}")


@dataclass(frozen=True)
class RollingContentValidationResult:
    ok: bool
    reason_code: str | None
    normalized_text: str


def validate(text: str) -> RollingContentValidationResult:
    normalized = str(text or "").strip()
    if not normalized:
        return RollingContentValidationResult(ok=False, reason_code="rolling_content_empty", normalized_text="")

    lowered = normalized.lower()
    if lowered in _PLACEHOLDER_EXACT_MATCHES:
        return RollingContentValidationResult(
            ok=False,
            reason_code="rolling_content_placeholder_exact",
            normalized_text=normalized,
        )

    if _PLACEHOLDER_TOKEN_PATTERN.search(normalized):
        return RollingContentValidationResult(
            ok=False,
            reason_code="rolling_content_placeholder_marker",
            normalized_text=normalized,
        )

    if _SEMANTIC_NOISE_PATTERN.search(lowered):
        return RollingContentValidationResult(
            ok=False,
            reason_code="rolling_content_semantic_noise",
            normalized_text=normalized,
        )

    if _REPEATED_CHAR_PATTERN.search(normalized):
        return RollingContentValidationResult(
            ok=False,
            reason_code="rolling_content_repeated_chars",
            normalized_text=normalized,
        )

    words = re.findall(r"[A-Za-zА-Яа-я0-9]+", normalized, flags=re.UNICODE)
    if len(words) < 3:
        return RollingContentValidationResult(
            ok=False,
            reason_code="rolling_content_low_information_density",
            normalized_text=normalized,
        )

    return RollingContentValidationResult(ok=True, reason_code=None, normalized_text=normalized)

