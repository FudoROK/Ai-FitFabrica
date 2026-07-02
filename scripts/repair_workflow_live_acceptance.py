"""Run repair workflow acceptance with real image edit and second quality verification."""

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

from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.adapters.try_on.provider_repair_adapter import ProviderRuntimeTryOnRepairAdapter
from src.adapters.try_on.repair_agent_planner import TryOnRepairAgentPlanner
from src.adapters.agents.adk_agent_gateway import AdkAgentGateway
from src.adapters.agents.in_memory_repository import InMemoryAgentInvocationRepository
from src.adapters.agents.object_storage_artifact_resolver import ObjectStorageAgentArtifactResolver
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStoredInput,
    TryOnUploadRole,
    TryOnWorkflowType,
)
from src.llm.provider_runtime import build_provider_runtime
from src.services.runtime.portable_infrastructure import build_portable_infrastructure
from src.settings import Settings, load_settings, validate_settings
from src.use_cases.agents.invocation_service import AgentInvocationService


def _parser() -> argparse.ArgumentParser:
    """Build CLI parser for the real repair workflow acceptance."""
    parser = argparse.ArgumentParser(description="Run real image-edit repair plus second Quality Verifier.")
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=Path("test-assets/quality-verifier/minor_background_artifact"),
        help="Case directory with generated_result.png, human_source.png, and garment_source.png.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/repair_workflow_live_acceptance_<timestamp>.jsonl.",
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


async def _run_acceptance(*, settings, case_dir: Path) -> tuple[dict[str, object], dict[str, object]]:
    """Run one repair workflow acceptance case."""
    if getattr(settings, "image_editing_provider", "stub") != "google_genai":
        raise RuntimeError("repair workflow live acceptance requires IMAGE_EDITING_PROVIDER=google_genai")
    storage = _build_object_storage(settings)
    providers = build_provider_runtime(settings, object_storage=storage)
    if providers.image_editing is None or getattr(providers.image_editing, "provider_name", "") == "stub_image_editing":
        raise RuntimeError("configured provider runtime does not expose real image_editing")
    if providers.agent_runtime is None:
        raise RuntimeError("repair workflow live acceptance requires agent_runtime for Repair Agent planner")

    root_prefix = getattr(settings, "image_editing_root_prefix", "fitfabrica")
    job_id = "repair_workflow_live_acceptance"
    assets = _store_case_assets(storage=storage, root_prefix=root_prefix, case_dir=case_dir, job_id=job_id)
    result = _initial_result(job_id=job_id, object_key=str(assets["generated_result"]["object_key"]), storage=storage)
    input_metadata = _input_metadata(assets=assets)
    stored_inputs = _stored_inputs(assets=assets, storage_backend=getattr(settings, "object_storage_backend", "in_memory"))
    invocation_service = AgentInvocationService(
        gateway=AdkAgentGateway(
            agent_runtime=providers.agent_runtime,
            artifact_resolver=ObjectStorageAgentArtifactResolver(
                object_storage=storage,
                max_artifact_bytes=int(getattr(settings, "try_on_max_upload_bytes", 10 * 1024 * 1024)),
            ),
        ),
        repository=InMemoryAgentInvocationRepository(),
    )
    repair_instruction_planner = TryOnRepairAgentPlanner(
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=float(getattr(settings, "try_on_repair_agent_timeout_seconds", 90.0)),
        preferred_model=getattr(settings, "try_on_repair_agent_preferred_model", None),
    )

    repair_adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=providers.image_editing,
        object_storage=storage,
        tenant_id="public",
        root_prefix=root_prefix,
        signed_url_ttl_seconds=int(getattr(settings, "object_storage_signed_url_ttl_seconds", 900)),
        repair_instruction_planner=repair_instruction_planner,
    )
    repaired_result = await repair_adapter.repair(
        job_id=job_id,
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        stored_inputs=stored_inputs,
        result=result,
        quality_report=result.quality_report,
    )

    second_verifier = DeterministicTryOnQualityVerifier(object_storage=storage)
    second_quality_report = await second_verifier.verify(
        job_id=job_id,
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=repaired_result,
    )
    repaired_object_key = repaired_result.result_image._artifact_object_key
    repaired_bytes = storage.get_bytes(repaired_object_key) if repaired_object_key else b""
    provider_name = getattr(providers.image_editing, "provider_name", "unknown")
    provider_repair_check = any(check.name == "provider_runtime_repair_applied" for check in repaired_result.quality_report.checks)
    repair_agent_blocked = any(check.name in {"repair_agent_blocked", "repair_agent_unavailable"} for check in repaired_result.quality_report.checks)
    passed = bool(repaired_bytes) and provider_repair_check and second_quality_report.verdict == "pass"

    row = {
        "case": case_dir.name,
        "provider": provider_name,
        "initial_quality_verdict": result.quality_report.verdict,
        "repair_artifact_object_key": repaired_object_key,
        "repair_artifact_size_bytes": len(repaired_bytes),
        "provider_repair_check": provider_repair_check,
        "repair_agent_blocked": repair_agent_blocked,
        "second_quality_verdict": second_quality_report.verdict,
        "second_quality_confidence": second_quality_report.confidence,
        "passed": passed,
    }
    summary = {
        "passed": passed,
        "provider": provider_name,
        "repair_artifact_object_key": repaired_object_key,
        "repair_artifact_size_bytes": len(repaired_bytes),
        "repair_agent_blocked": repair_agent_blocked,
        "second_quality_verdict": second_quality_report.verdict,
        "second_quality_confidence": second_quality_report.confidence,
    }
    return row, summary


def _store_case_assets(*, storage, root_prefix: str, case_dir: Path, job_id: str) -> dict[str, dict[str, object]]:
    """Store source, human, and garment case images in backend object storage."""
    required = {
        "generated_result": case_dir / "generated_result.png",
        "human_source": case_dir / "human_source.png",
        "garment_source": case_dir / "garment_source.png",
    }
    assets: dict[str, dict[str, object]] = {}
    for role, path in required.items():
        assets[role] = _put_asset(storage=storage, root_prefix=root_prefix, job_id=job_id, role=role, path=path)
    return assets


def _put_asset(*, storage, root_prefix: str, job_id: str, role: str, path: Path) -> dict[str, object]:
    """Persist one local image asset and return metadata used by workflow ports."""
    if not path.is_file():
        raise ValueError(f"required repair acceptance asset is missing: {path}")
    payload = path.read_bytes()
    content_type = _content_type(path)
    digest = sha256(payload).hexdigest()
    object_key = f"{root_prefix}/acceptance/repair-workflow/{job_id}/{role}/{digest[:16]}-{path.name}"
    stored = storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    signed_url = storage.create_signed_get_url(stored.object_key, expires_in_seconds=900)
    return {
        "object_key": stored.object_key,
        "uri": signed_url.url,
        "content_type": stored.content_type,
        "size_bytes": stored.content_length,
        "sha256": digest,
    }


def _initial_result(*, job_id: str, object_key: str, storage) -> TryOnResult:
    """Build an initial result that must go through local repair."""
    signed_url = storage.create_signed_get_url(object_key, expires_in_seconds=900)
    result_image = TryOnResultImage(kind="generated_artifact", url=signed_url.url, alt="Generated Try-On result")
    result_image._artifact_object_key = object_key
    return TryOnResult(
        job_id=job_id,
        workflow_type=TryOnWorkflowType.TRY_ON,
        result_image=result_image,
        quality_report=TryOnQualityReport(
            verdict="repair_recommended",
            confidence=0.82,
            checks=[
                TryOnQualityCheck(
                    name="background_artifact",
                    status="warning",
                    confidence=0.82,
                    message="Small local background artifact should be repaired before exposure.",
                )
            ],
            limitations=["Local background cleanup required."],
        ),
        stylist_note="Generated result requires local repair.",
        input_metadata=[],
    )


def _input_metadata(*, assets: dict[str, dict[str, object]]) -> list[TryOnInputMetadata]:
    """Build input metadata for the second Quality Verifier."""
    return [
        TryOnInputMetadata(
            role=TryOnUploadRole.HUMAN_PHOTO,
            filename="human_source.png",
            content_type=str(assets["human_source"]["content_type"]),
            size_bytes=int(assets["human_source"]["size_bytes"]),
            sha256=str(assets["human_source"]["sha256"]),
        ),
        TryOnInputMetadata(
            role=TryOnUploadRole.GARMENT_PHOTO,
            filename="garment_source.png",
            content_type=str(assets["garment_source"]["content_type"]),
            size_bytes=int(assets["garment_source"]["size_bytes"]),
            sha256=str(assets["garment_source"]["sha256"]),
        ),
    ]


def _stored_inputs(*, assets: dict[str, dict[str, object]], storage_backend: str) -> list[TryOnStoredInput]:
    """Build stored input references for repair and second Quality Verifier."""
    return [
        TryOnStoredInput(
            role=TryOnUploadRole.HUMAN_PHOTO,
            storage_backend=storage_backend,
            uri=str(assets["human_source"]["uri"]),
            object_key=str(assets["human_source"]["object_key"]),
            object_name=str(assets["human_source"]["object_key"]),
            content_type=str(assets["human_source"]["content_type"]),
            size_bytes=int(assets["human_source"]["size_bytes"]),
            sha256=str(assets["human_source"]["sha256"]),
        ),
        TryOnStoredInput(
            role=TryOnUploadRole.GARMENT_PHOTO,
            storage_backend=storage_backend,
            uri=str(assets["garment_source"]["uri"]),
            object_key=str(assets["garment_source"]["object_key"]),
            object_name=str(assets["garment_source"]["object_key"]),
            content_type=str(assets["garment_source"]["content_type"]),
            size_bytes=int(assets["garment_source"]["size_bytes"]),
            sha256=str(assets["garment_source"]["sha256"]),
        ),
    ]


def _content_type(path: Path) -> str:
    """Return supported image content type for an acceptance asset."""
    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    raise ValueError(f"unsupported image type for repair acceptance asset: {path.name}")


def _output_path(path: Path | None) -> Path:
    """Resolve JSONL output path."""
    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"repair_workflow_live_acceptance_{timestamp}.jsonl"


def _write_jsonl(*, output_path: Path, row: dict[str, object], summary: dict[str, object]) -> None:
    """Write acceptance row and summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "case", **row}, ensure_ascii=False) + "\n")
        handle.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Run the repair workflow live acceptance CLI."""
    args = _parser().parse_args(argv)
    try:
        settings = _load_settings(env_file=args.env_file)
        row, summary = asyncio.run(_run_acceptance(settings=settings, case_dir=args.case_dir))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, row=row, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("repair_workflow_live_acceptance_status=error")
        print(f"error={exc}")
        return 1

    print("repair_workflow_live_acceptance_status=completed")
    print(f"output={output_path}")
    print(f"passed={summary['passed']}")
    print(f"provider={summary['provider']}")
    print(f"repair_artifact_size_bytes={summary['repair_artifact_size_bytes']}")
    print(f"second_quality_verdict={summary['second_quality_verdict']}")
    if args.require_pass and summary["passed"] is not True:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
