from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


class _FakeVertexClient:
    provider_name = "vertex_virtual_try_on"

    def generate(
        self,
        *,
        person_image_bytes: bytes,
        person_image_mime_type: str,
        garment_image_bytes: bytes,
        garment_image_mime_type: str,
        prompt: str,
    ) -> tuple[bytes, str]:
        assert person_image_bytes
        assert garment_image_bytes
        assert person_image_mime_type == "image/png"
        assert garment_image_mime_type == "image/png"
        assert prompt
        return b"generated-try-on-bytes" * 1000, "image/png"


def test_try_on_generation_live_smoke_writes_summary(tmp_path, monkeypatch) -> None:
    from scripts import try_on_generation_live_smoke
    from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage

    human = tmp_path / "human.png"
    garment = tmp_path / "garment.png"
    output = tmp_path / "try-on-generation.jsonl"
    human.write_bytes(b"human-image-bytes")
    garment.write_bytes(b"garment-image-bytes")
    storage = InMemoryObjectStorage()

    monkeypatch.setattr(
        try_on_generation_live_smoke,
        "_load_settings",
        lambda env_file: SimpleNamespace(
            vertex_project="project-id",
            vertex_virtual_try_on_location="global",
            vertex_virtual_try_on_model="virtual-try-on-test",
            object_storage_prefix="fitfabrica-test",
            object_storage_signed_url_ttl_seconds=900,
            object_storage_backend="in_memory",
        ),
    )
    monkeypatch.setattr(try_on_generation_live_smoke, "_build_object_storage", lambda settings: storage)
    monkeypatch.setattr(
        try_on_generation_live_smoke,
        "VertexVirtualTryOnClient",
        lambda **_kwargs: _FakeVertexClient(),
    )

    exit_code = try_on_generation_live_smoke.main(
        [
            "--human",
            str(human),
            "--garment",
            str(garment),
            "--output",
            str(output),
            "--require-pass",
        ]
    )

    assert exit_code == 0
    rows = output.read_text(encoding="utf-8").splitlines()
    assert '"type": "summary"' in rows[-1]
    assert '"passed": true' in rows[-1]
    assert '"generation_mode": "vertex_virtual_try_on"' in rows[-1]
    assert '"result_artifact_size_bytes": 22000' in rows[-1]
