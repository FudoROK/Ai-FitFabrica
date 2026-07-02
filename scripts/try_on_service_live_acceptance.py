"""Run end-to-end Try-On service acceptance with real Vertex generation."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from starlette.datastructures import UploadFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.adapters.agents.deterministic_human_identity_analysis import DeterministicHumanIdentityAnalysisAdapter
from src.adapters.agents.deterministic_try_on_garment_identity_analysis import (
    DeterministicTryOnGarmentIdentityAnalysisAdapter,
)
from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from src.adapters.agents.deterministic_try_on_material_texture_analysis import (
    DeterministicTryOnMaterialTextureAnalysisAdapter,
)
from src.adapters.ai.vertex_virtual_try_on_client import VertexVirtualTryOnClient
from src.adapters.storage.media_storage import TryOnMediaStorage
from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.adapters.try_on.deterministic_stylist import DeterministicTryOnStylist
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.adapters.try_on.vertex_virtual_try_on_generation import VertexVirtualTryOnGenerationAdapter
from src.services.runtime.portable_infrastructure import build_portable_infrastructure
from src.settings import Settings, load_settings, validate_settings
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundleService
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


def _parser() -> argparse.ArgumentParser:
    """Build CLI parser for the service-level Try-On live acceptance."""
    parser = argparse.ArgumentParser(description="Run Try-On service acceptance with real Vertex generation.")
    parser.add_argument("--human", type=Path, required=True, help="Human/person image.")
    parser.add_argument("--garment", type=Path, required=True, help="Garment/product image.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/try_on_service_live_acceptance_<timestamp>.jsonl.",
    )
    parser.add_argument("--require-pass", action="store_true", help="Exit non-zero when acceptance fails.")
    return parser


def _load_settings(*, env_file: Path | None):
    """Load validated settings from env or one explicit env file."""
    if env_file is None:
        return load_settings()
    settings = Settings(_env_file=str(env_file), _env_file_encoding="utf-8")
    validate_settings(settings)
    return settings


def _build_object_storage(settings):
    """Return runtime object storage for the acceptance script."""
    return build_portable_infrastructure(settings).object_storage


async def _run_acceptance(*, settings, human: Path, garment: Path) -> tuple[dict[str, object], dict[str, object]]:
    """Create and execute one Try-On job through the service lifecycle."""
    storage = _build_object_storage(settings)
    root_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    ttl_seconds = int(getattr(settings, "object_storage_signed_url_ttl_seconds", 900))
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=VertexVirtualTryOnGenerationAdapter(
            object_storage=storage,
            tenant_id="public",
            root_prefix=root_prefix,
            signed_url_ttl_seconds=ttl_seconds,
            vertex_client=VertexVirtualTryOnClient(
                project=getattr(settings, "vertex_project", "") or "",
                location=getattr(settings, "vertex_virtual_try_on_location", "global") or "global",
                model=getattr(settings, "vertex_virtual_try_on_model", "virtual-try-on-001"),
            ),
        ),
        analysis_bundle_service=TryOnAnalysisBundleService(
            human_identity_analyzer=DeterministicHumanIdentityAnalysisAdapter(),
            garment_identity_analyzer=DeterministicTryOnGarmentIdentityAnalysisAdapter(),
            material_texture_analyzer=DeterministicTryOnMaterialTextureAnalysisAdapter(),
        ),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        repair_adapter=None,
        stylist_adapter=DeterministicTryOnStylist(),
        file_storage=TryOnMediaStorage(object_storage=storage, tenant_id="public", root_prefix=root_prefix),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types=set(getattr(settings, "try_on_allowed_content_types", ["image/jpeg", "image/png", "image/webp"])),
            max_upload_bytes=int(getattr(settings, "try_on_max_upload_bytes", 10 * 1024 * 1024)),
        ),
    )
    job = await service.create_job(
        human_photo=_upload_file(human),
        garment_photo=_upload_file(garment),
    )
    completed = await service.execute_job(job_id=job.job_id)
    result_object_key = completed.result.result_image._artifact_object_key if completed.result is not None else None
    result_bytes = storage.get_bytes(result_object_key) if result_object_key else b""
    quality_verdict = completed.result.quality_report.verdict if completed.result is not None else None
    passed = completed.status.value == "completed" and bool(result_bytes) and quality_verdict == "pass"
    row = {
        "job_id": completed.job_id,
        "final_status": completed.status.value,
        "generation_mode": completed.generation_mode.value,
        "result_object_key": result_object_key,
        "result_artifact_size_bytes": len(result_bytes),
        "quality_verdict": quality_verdict,
        "status_history": [event.status.value for event in completed.status_history],
        "passed": passed,
    }
    summary = {
        "passed": passed,
        "job_id": completed.job_id,
        "final_status": completed.status.value,
        "generation_mode": completed.generation_mode.value,
        "result_object_key": result_object_key,
        "result_artifact_size_bytes": len(result_bytes),
        "quality_verdict": quality_verdict,
    }
    return row, summary


def _upload_file(path: Path) -> UploadFile:
    """Build an UploadFile from a local image path for the service API."""
    if not path.is_file():
        raise ValueError(f"Try-On service acceptance asset does not exist: {path}")
    content_type = _content_type(path)
    return UploadFile(filename=path.name, file=BytesIO(path.read_bytes()), headers={"content-type": content_type})


def _content_type(path: Path) -> str:
    """Return supported image content type from filename extension."""
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    raise ValueError(f"unsupported Try-On service acceptance image type: {path.name}")


def _output_path(path: Path | None) -> Path:
    """Resolve JSONL output path."""
    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"try_on_service_live_acceptance_{timestamp}.jsonl"


def _write_jsonl(*, output_path: Path, row: dict[str, object], summary: dict[str, object]) -> None:
    """Write acceptance row and summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "case", **row}, ensure_ascii=False) + "\n")
        handle.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Run the Try-On service live acceptance CLI."""
    args = _parser().parse_args(argv)
    try:
        settings = _load_settings(env_file=args.env_file)
        row, summary = asyncio.run(_run_acceptance(settings=settings, human=args.human, garment=args.garment))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, row=row, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("try_on_service_live_acceptance_status=error")
        print(f"error={exc}")
        return 1

    print("try_on_service_live_acceptance_status=completed")
    print(f"output={output_path}")
    print(f"passed={summary['passed']}")
    print(f"job_id={summary['job_id']}")
    print(f"final_status={summary['final_status']}")
    print(f"generation_mode={summary['generation_mode']}")
    print(f"result_artifact_size_bytes={summary['result_artifact_size_bytes']}")
    print(f"quality_verdict={summary['quality_verdict']}")
    if args.require_pass and summary["passed"] is not True:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
