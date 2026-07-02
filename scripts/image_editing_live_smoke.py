"""Run one real image-editing provider smoke through the backend ImageEditingPort."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.domain.provider_models import ImageEditingRequest
from src.llm.provider_runtime import build_provider_runtime
from src.services.runtime.portable_infrastructure import build_portable_infrastructure
from src.settings import Settings, load_settings, validate_settings


def _parser() -> argparse.ArgumentParser:
    """Build CLI parser for one real image-editing smoke."""
    parser = argparse.ArgumentParser(description="Run one image-editing provider smoke through ImageEditingPort.")
    parser.add_argument("--source", type=Path, required=True, help="Source image to edit.")
    parser.add_argument(
        "--reference",
        type=Path,
        action="append",
        default=[],
        help="Optional reference image. Can be passed multiple times.",
    )
    parser.add_argument(
        "--prompt",
        default=(
            "Apply a tiny local cleanup only. Preserve identity, pose, garment shape, color, and all important details."
        ),
        help="Provider prompt for the smoke edit.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/image_editing_live_smoke_<timestamp>.jsonl.",
    )
    parser.add_argument("--require-pass", action="store_true", help="Exit non-zero when smoke validation fails.")
    return parser


def _load_settings(*, env_file: Path | None):
    """Load validated settings from env or one explicit env file."""
    if env_file is None:
        return load_settings()
    settings = Settings(_env_file=str(env_file), _env_file_encoding="utf-8")
    validate_settings(settings)
    return settings


def _build_object_storage(settings):
    """Return runtime object storage for the smoke script."""
    return build_portable_infrastructure(settings).object_storage


def _content_type(path: Path) -> str:
    """Return supported image content type for a local smoke asset."""
    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    raise ValueError(f"unsupported image type for smoke asset: {path.name}")


def _put_asset(*, storage, root_prefix: str, role: str, path: Path) -> dict[str, object]:
    """Store a local smoke asset under a backend-owned object key."""
    if not path.is_file():
        raise ValueError(f"image asset does not exist: {path}")
    payload = path.read_bytes()
    content_type = _content_type(path)
    digest = sha256(payload).hexdigest()
    object_key = f"{root_prefix}/acceptance/image-editing/{role}/{digest[:16]}-{path.name}"
    stored = storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    return {
        "object_key": stored.object_key,
        "content_type": stored.content_type,
        "size_bytes": stored.content_length,
        "sha256": digest,
    }


def _output_path(path: Path | None) -> Path:
    """Resolve JSONL output path."""
    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"image_editing_live_smoke_{timestamp}.jsonl"


def _write_jsonl(*, output_path: Path, row: dict[str, object], summary: dict[str, object]) -> None:
    """Write smoke row and summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "case", **row}, ensure_ascii=False) + "\n")
        handle.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")


def _run_smoke(*, settings, source: Path, references: list[Path], prompt: str) -> tuple[dict[str, object], dict[str, object]]:
    """Run one image-edit smoke through the configured provider runtime."""
    if getattr(settings, "image_editing_provider", "stub") != "google_genai":
        raise RuntimeError("image editing live smoke requires IMAGE_EDITING_PROVIDER=google_genai")
    storage = _build_object_storage(settings)
    root_prefix = getattr(settings, "image_editing_root_prefix", "fitfabrica")
    source_asset = _put_asset(storage=storage, root_prefix=root_prefix, role="source", path=source)
    reference_assets = [
        _put_asset(storage=storage, root_prefix=root_prefix, role=f"reference-{index}", path=path)
        for index, path in enumerate(references, start=1)
    ]
    providers = build_provider_runtime(settings, object_storage=storage)
    if providers.image_editing is None:
        raise RuntimeError("configured provider runtime does not expose image_editing")
    edit_result = providers.image_editing.edit(
        ImageEditingRequest(
            task="image_editing_live_smoke",
            prompt=prompt,
            source_object_key=str(source_asset["object_key"]),
            reference_object_keys=[str(asset["object_key"]) for asset in reference_assets],
            output_mime_type="image/png",
        )
    )
    edited_bytes = storage.get_bytes(edit_result.output_object_key)
    passed = bool(edited_bytes) and edit_result.provider != "stub_image_editing"
    row = {
        "source": source_asset,
        "references": reference_assets,
        "provider": edit_result.provider,
        "output_object_key": edit_result.output_object_key,
        "output_mime_type": edit_result.output_mime_type,
        "output_size_bytes": len(edited_bytes),
        "passed": passed,
    }
    summary = {
        "passed": passed,
        "provider": edit_result.provider,
        "output_object_key": edit_result.output_object_key,
        "output_size_bytes": len(edited_bytes),
    }
    return row, summary


def main(argv: list[str] | None = None) -> int:
    """Run the image-editing live smoke CLI."""
    args = _parser().parse_args(argv)
    try:
        settings = _load_settings(env_file=args.env_file)
        row, summary = _run_smoke(
            settings=settings,
            source=args.source,
            references=list(args.reference),
            prompt=args.prompt,
        )
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, row=row, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("image_editing_live_smoke_status=error")
        print(f"error={exc}")
        return 1

    print("image_editing_live_smoke_status=completed")
    print(f"output={output_path}")
    print(f"passed={summary['passed']}")
    print(f"provider={summary['provider']}")
    print(f"output_size_bytes={summary['output_size_bytes']}")
    if args.require_pass and summary["passed"] is not True:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
