from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


class _ProviderRuntime:
    def __init__(self, image_editing) -> None:
        self.image_editing = image_editing


class _ImageEditingProvider:
    provider_name = "google_genai_image_editing"

    def __init__(self, *, storage) -> None:
        self._storage = storage

    def edit(self, request):
        from src.domain.provider_models import ImageEditingResult

        output_key = "provider-artifacts/image-editing/live-smoke/edited.webp"
        self._storage.put_bytes(
            object_key=output_key,
            payload=b"edited-live-smoke-bytes",
            content_type=request.output_mime_type,
        )
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=output_key,
            output_mime_type=request.output_mime_type,
            provider=self.provider_name,
        )


def test_image_editing_live_smoke_writes_summary(tmp_path, monkeypatch) -> None:
    from scripts import image_editing_live_smoke
    from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage

    source = tmp_path / "source.png"
    reference = tmp_path / "reference.png"
    output = tmp_path / "smoke.jsonl"
    source.write_bytes(b"source-image-bytes")
    reference.write_bytes(b"reference-image-bytes")
    storage = InMemoryObjectStorage()

    monkeypatch.setattr(
        image_editing_live_smoke,
        "_load_settings",
        lambda env_file: SimpleNamespace(image_editing_provider="google_genai"),
    )
    monkeypatch.setattr(
        image_editing_live_smoke,
        "_build_object_storage",
        lambda settings: storage,
    )
    monkeypatch.setattr(
        image_editing_live_smoke,
        "build_provider_runtime",
        lambda settings, object_storage: _ProviderRuntime(_ImageEditingProvider(storage=object_storage)),
    )

    exit_code = image_editing_live_smoke.main(
        [
            "--source",
            str(source),
            "--reference",
            str(reference),
            "--output",
            str(output),
            "--require-pass",
        ]
    )

    assert exit_code == 0
    rows = output.read_text(encoding="utf-8").splitlines()
    assert '"type": "summary"' in rows[-1]
    assert '"passed": true' in rows[-1]
    assert '"provider": "google_genai_image_editing"' in rows[-1]
