"""Run one real Vertex Virtual Try-On generation smoke through the backend adapter."""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.adapters.ai.vertex_virtual_try_on_client import VertexVirtualTryOnClient
from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.adapters.try_on.vertex_virtual_try_on_generation import VertexVirtualTryOnGenerationAdapter
from src.domain.try_on import TryOnInputMetadata, TryOnStoredInput, TryOnUploadRole
from src.domain.try_on_instruction import TryOnGenerationInstruction
from src.services.runtime.portable_infrastructure import build_portable_infrastructure
from src.settings import Settings, load_settings, validate_settings


def _parser() -> argparse.ArgumentParser:
    """Build CLI parser for one real Try-On generation smoke."""
    parser = argparse.ArgumentParser(description="Run one real Vertex Virtual Try-On generation smoke.")
    parser.add_argument("--human", type=Path, required=True, help="Human/person image.")
    parser.add_argument("--garment", type=Path, required=True, help="Garment/product image.")
    parser.add_argument(
        "--prompt",
        default=(
            "Create a realistic virtual try-on image. Preserve the person's identity, body proportions, pose, "
            "and the garment color, cut, silhouette, and visible details."
        ),
        help="Generation instruction summary.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/try_on_generation_live_smoke_<timestamp>.jsonl.",
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


async def _run_smoke(
    *,
    settings,
    human: Path,
    garment: Path,
    prompt: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Run one real Try-On generation and deterministic artifact verification."""
    storage = _build_object_storage(settings)
    root_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    ttl_seconds = int(getattr(settings, "object_storage_signed_url_ttl_seconds", 900))
    job_id = "try_on_generation_live_smoke"
    human_asset = _put_asset(storage=storage, root_prefix=root_prefix, job_id=job_id, role="human_photo", path=human)
    garment_asset = _put_asset(
        storage=storage,
        root_prefix=root_prefix,
        job_id=job_id,
        role="garment_photo",
        path=garment,
    )
    input_metadata = _input_metadata(human_asset=human_asset, garment_asset=garment_asset)
    stored_inputs = _stored_inputs(
        human_asset=human_asset,
        garment_asset=garment_asset,
        storage_backend=getattr(settings, "object_storage_backend", "in_memory"),
    )
    adapter = VertexVirtualTryOnGenerationAdapter(
        object_storage=storage,
        tenant_id="public",
        root_prefix=root_prefix,
        signed_url_ttl_seconds=ttl_seconds,
        vertex_client=VertexVirtualTryOnClient(
            project=getattr(settings, "vertex_project", "") or "",
            location=getattr(settings, "vertex_virtual_try_on_location", "global") or "global",
            model=getattr(settings, "vertex_virtual_try_on_model", "virtual-try-on-001"),
        ),
    )
    result = await adapter.generate(
        job_id=job_id,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        instruction=TryOnGenerationInstruction(
            invocation_id="try-on-generation-live-smoke",
            prompt_version="try_on.live_smoke.v1",
            contract_version="try_on.contract.v2",
            instruction_summary=prompt,
            confidence=0.9,
            uncertainty_level="low",
        ),
    )
    result_object_key = result.result_image._artifact_object_key
    result_bytes = storage.get_bytes(result_object_key) if result_object_key else b""
    verifier = DeterministicTryOnQualityVerifier(object_storage=storage)
    quality_report = await verifier.verify(
        job_id=job_id,
        generation_mode=adapter.generation_mode,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=result,
    )
    passed = bool(result_bytes) and quality_report.verdict == "pass"
    row = {
        "generation_mode": adapter.generation_mode.value,
        "result_object_key": result_object_key,
        "result_artifact_size_bytes": len(result_bytes),
        "quality_verdict": quality_report.verdict,
        "quality_confidence": quality_report.confidence,
        "passed": passed,
    }
    summary = dict(row)
    return row, summary


def _put_asset(*, storage, root_prefix: str, job_id: str, role: str, path: Path) -> dict[str, object]:
    """Persist one local smoke asset and return workflow metadata."""
    if not path.is_file():
        raise ValueError(f"Try-On smoke asset does not exist: {path}")
    payload = path.read_bytes()
    content_type = _content_type(path)
    digest = sha256(payload).hexdigest()
    object_key = f"{root_prefix}/acceptance/try-on-generation/{job_id}/{role}/{digest[:16]}-{path.name}"
    stored = storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    signed_url = storage.create_signed_get_url(stored.object_key, expires_in_seconds=900)
    return {
        "object_key": stored.object_key,
        "uri": signed_url.url,
        "content_type": stored.content_type,
        "size_bytes": stored.content_length,
        "sha256": digest,
        "filename": path.name,
    }


def _input_metadata(*, human_asset: dict[str, object], garment_asset: dict[str, object]) -> list[TryOnInputMetadata]:
    """Build Try-On input metadata for the generation adapter."""
    return [
        TryOnInputMetadata(
            role=TryOnUploadRole.HUMAN_PHOTO,
            filename=str(human_asset["filename"]),
            content_type=str(human_asset["content_type"]),
            size_bytes=int(human_asset["size_bytes"]),
            sha256=str(human_asset["sha256"]),
        ),
        TryOnInputMetadata(
            role=TryOnUploadRole.GARMENT_PHOTO,
            filename=str(garment_asset["filename"]),
            content_type=str(garment_asset["content_type"]),
            size_bytes=int(garment_asset["size_bytes"]),
            sha256=str(garment_asset["sha256"]),
        ),
    ]


def _stored_inputs(
    *,
    human_asset: dict[str, object],
    garment_asset: dict[str, object],
    storage_backend: str,
) -> list[TryOnStoredInput]:
    """Build stored input references for the generation adapter."""
    return [
        TryOnStoredInput(
            role=TryOnUploadRole.HUMAN_PHOTO,
            storage_backend=storage_backend,
            uri=str(human_asset["uri"]),
            object_key=str(human_asset["object_key"]),
            object_name=str(human_asset["object_key"]),
            content_type=str(human_asset["content_type"]),
            size_bytes=int(human_asset["size_bytes"]),
            sha256=str(human_asset["sha256"]),
        ),
        TryOnStoredInput(
            role=TryOnUploadRole.GARMENT_PHOTO,
            storage_backend=storage_backend,
            uri=str(garment_asset["uri"]),
            object_key=str(garment_asset["object_key"]),
            object_name=str(garment_asset["object_key"]),
            content_type=str(garment_asset["content_type"]),
            size_bytes=int(garment_asset["size_bytes"]),
            sha256=str(garment_asset["sha256"]),
        ),
    ]


def _content_type(path: Path) -> str:
    """Return one supported image content type for a smoke asset."""
    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    raise ValueError(f"unsupported image type for Try-On smoke asset: {path.name}")


def _output_path(path: Path | None) -> Path:
    """Resolve JSONL output path."""
    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"try_on_generation_live_smoke_{timestamp}.jsonl"


def _write_jsonl(*, output_path: Path, row: dict[str, object], summary: dict[str, object]) -> None:
    """Write smoke row and summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "case", **row}, ensure_ascii=False) + "\n")
        handle.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Run the Try-On generation live smoke CLI."""
    args = _parser().parse_args(argv)
    try:
        settings = _load_settings(env_file=args.env_file)
        row, summary = asyncio.run(_run_smoke(settings=settings, human=args.human, garment=args.garment, prompt=args.prompt))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, row=row, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("try_on_generation_live_smoke_status=error")
        print(f"error={exc}")
        return 1

    print("try_on_generation_live_smoke_status=completed")
    print(f"output={output_path}")
    print(f"passed={summary['passed']}")
    print(f"generation_mode={summary['generation_mode']}")
    print(f"result_artifact_size_bytes={summary['result_artifact_size_bytes']}")
    print(f"quality_verdict={summary['quality_verdict']}")
    if args.require_pass and summary["passed"] is not True:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
