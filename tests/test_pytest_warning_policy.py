"""Guardrails for pytest warning policy."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_authlib_joserfc_compat_warning_is_filtered_narrowly() -> None:
    """Authlib's third-party compatibility warning should be the only ignored deprecation."""

    config = (PROJECT_ROOT / "pytest.ini").read_text(encoding="utf-8")

    assert "filterwarnings =" in config
    assert (
        "ignore:authlib\\.jose module is deprecated, please use joserfc instead\\.:"
        "authlib.deprecate.AuthlibDeprecationWarning:authlib\\._joserfc_helpers"
    ) in config
    assert "ignore::DeprecationWarning" not in config
    assert "ignore::Warning" not in config
