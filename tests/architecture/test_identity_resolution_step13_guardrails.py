from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_hot_path_no_channel_derived_lead_id_in_inbound_gate() -> None:
    text = _read("src/services/inbound/inbound_gate_service.py")
    assert "get_or_create_canonical(" in text
    assert 'f"{identity.channel}:{identity.external_user_id}"' not in text


def test_runtime_has_explicit_identity_resolution_boundary() -> None:
    text = _read("src/identity_core/services/identity_resolution.py")
    assert "class RuntimeIdentityResolutionService" in text
    assert "ChannelIdentityRepository" in text
    assert "IdentityBindingRepository" in text
    assert "LeadRepository" in text


def test_context_builder_uses_canonical_lead_id_parameter() -> None:
    text = _read("src/services/context/core_context_builder.py")
    assert "lead_id: str" in text
    assert 'lead_id = f"{safe_channel}:{safe_external_id}"' not in text


def test_dialog_service_no_longer_selects_production_identity_backend_directly() -> None:
    text = _read("src/services/dialog/dialog_service.py")
    assert "FirestoreChannelIdentityRepository" not in text
    assert "FirestoreIdentityBindingRepository" not in text
    assert "FirestoreLeadIdentityRepository" not in text
    assert "SqlChannelIdentityRepository" not in text
    assert "SqlIdentityBindingRepository" not in text
    assert "SqlLeadRepository" not in text
