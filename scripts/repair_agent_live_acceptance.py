"""Run Repair Agent live acceptance without executing image editing."""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.adapters.agents.adk_agent_gateway import AdkAgentGateway
from src.adapters.agents.in_memory_repository import InMemoryAgentInvocationRepository
from src.adapters.agents.object_storage_artifact_resolver import ObjectStorageAgentArtifactResolver
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adk_agents.repair_agent.contracts import RepairAgentRequest, RepairDefectInput, RepairInstructionContract
from src.adk_agents.repair_agent.deploy_config import RepairAgentDeployConfig
from src.adk_agents.repair_agent.prompt_config import REPAIR_AGENT_INSTRUCTION
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.llm.provider_runtime import build_provider_runtime
from src.settings import Settings, load_settings, validate_settings
from src.use_cases.agents.invocation_service import AgentInvocationService

REQUIRED_CASES = (
    "face_changed",
    "minor_background_artifact",
    "minor_color_shift",
    "severe_anatomy_artifact",
)

_EXPECTED_SCOPES = {
    "minor_background_artifact": "local",
    "minor_color_shift": "local",
    "face_changed": "unsafe",
    "severe_anatomy_artifact": "unsafe",
}


@dataclass(frozen=True)
class AcceptanceCase:
    """One named Repair Agent acceptance case."""

    name: str
    generated_result_path: Path
    expected_scope: str
    defects: list[RepairDefectInput]
    immutable_regions: list[str]


def expected_scope_for(case_name: str) -> str:
    """Return expected Repair Agent scope for a named case."""

    try:
        return _EXPECTED_SCOPES[case_name]
    except KeyError as exc:
        raise ValueError(f"unknown Repair Agent acceptance case: {case_name}") from exc


def collect_acceptance_cases(assets_dir: Path) -> list[AcceptanceCase]:
    """Return canonical Repair Agent cases from the quality-verifier visual dataset."""

    if not assets_dir.exists():
        raise ValueError(f"assets directory does not exist: {assets_dir}")
    cases: list[AcceptanceCase] = []
    for case_name in sorted(REQUIRED_CASES):
        case_dir = assets_dir / case_name
        if not case_dir.is_dir():
            raise ValueError(f"missing required repair case directory: {case_name}")
        generated_result_path = case_dir / "generated_result.png"
        if not generated_result_path.is_file():
            raise ValueError(f"missing generated_result.png for {case_name}")
        cases.append(
            AcceptanceCase(
                name=case_name,
                generated_result_path=generated_result_path,
                expected_scope=expected_scope_for(case_name),
                defects=_defects_for(case_name),
                immutable_regions=_immutable_regions_for(case_name),
            )
        )
    return cases


def _defects_for(case_name: str) -> list[RepairDefectInput]:
    """Return backend-approved defects for one acceptance case."""

    defects_by_case = {
        "minor_background_artifact": [
            RepairDefectInput(
                defect_type="background",
                region="upper right background",
                evidence="Small local background stain is visible while person, pose, and garment are preserved.",
            )
        ],
        "minor_color_shift": [
            RepairDefectInput(
                defect_type="color",
                region="garment body",
                evidence="Garment is slightly more blue than the approved green source while shape and identity are preserved.",
            )
        ],
        "face_changed": [
            RepairDefectInput(
                defect_type="face",
                region="face",
                evidence="Generated face identity changed and must not be locally repaired.",
            )
        ],
        "severe_anatomy_artifact": [
            RepairDefectInput(
                defect_type="hands",
                region="hands",
                evidence="Generated result has severe hand anatomy defects, including an extra or malformed hand.",
            )
        ],
    }
    return defects_by_case[case_name]


def _immutable_regions_for(case_name: str) -> list[str]:
    """Return regions that the repair plan must preserve."""

    immutable = ["face", "identity", "body_shape", "pose", "unrelated_garment_details"]
    if case_name == "minor_color_shift":
        return immutable + ["buttons", "collar", "silhouette"]
    return immutable


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run Repair Agent live acceptance only.")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path("test-assets/quality-verifier"),
        help="Quality Verifier dataset directory containing generated_result.png files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/repair_agent_live_acceptance_<timestamp>.jsonl.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Exit non-zero when scope mismatches are present.",
    )
    return parser


async def _run_acceptance(*, cases: list[AcceptanceCase], settings) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Invoke only Repair Agent against backend-approved defects."""

    providers = build_provider_runtime(settings)
    if providers.agent_runtime is None:
        raise RuntimeError("Repair Agent live acceptance requires llm.provider=vertex with agent_runtime enabled.")
    storage = InMemoryObjectStorage()
    gateway = AdkAgentGateway(
        agent_runtime=providers.agent_runtime,
        artifact_resolver=ObjectStorageAgentArtifactResolver(
            object_storage=storage,
            max_artifact_bytes=int(getattr(settings, "try_on_max_upload_bytes", 10 * 1024 * 1024)),
        ),
    )
    invocation_service = AgentInvocationService(
        gateway=gateway,
        repository=InMemoryAgentInvocationRepository(),
    )
    config = RepairAgentDeployConfig()
    preferred_model = getattr(settings, "try_on_repair_agent_preferred_model", None) or config.model
    timeout_seconds = float(getattr(settings, "try_on_repair_agent_timeout_seconds", 90.0))

    rows: list[dict[str, object]] = []
    for case in cases:
        rows.append(
            await _run_one_case(
                case=case,
                storage=storage,
                invocation_service=invocation_service,
                config=config,
                preferred_model=preferred_model,
                timeout_seconds=timeout_seconds,
            )
        )
    summary = _summarize(rows)
    return rows, summary


async def _run_one_case(
    *,
    case: AcceptanceCase,
    storage: InMemoryObjectStorage,
    invocation_service: AgentInvocationService,
    config: RepairAgentDeployConfig,
    preferred_model: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Run one Repair Agent case and return a JSONL-safe acceptance row."""

    artifact_ref = _store_generated_result(case=case, storage=storage)
    request_payload = RepairAgentRequest(
        generated_image_object_key=artifact_ref.object_key,
        approved_defects=case.defects,
        immutable_regions=case.immutable_regions,
    )
    envelope = await invocation_service.invoke(
        request=AgentInvocationRequest(
            agent_name=config.name,
            prompt_version=config.prompt_version,
            contract_version=config.contract_version,
            trace_id=f"repair-live-{case.name}",
            prompt=REPAIR_AGENT_INSTRUCTION,
            input_payload=request_payload.model_dump(mode="json"),
            artifact_references=[artifact_ref],
            response_schema=RepairInstructionContract.model_json_schema(),
            timeout_seconds=timeout_seconds,
            preferred_model=preferred_model,
        ),
        output_contract=RepairInstructionContract,
    )
    if (
        envelope.status != AgentRuntimeStatus.SUCCEEDED
        or envelope.validation_status != AgentValidationStatus.PASSED
        or envelope.output is None
    ):
        actual_scope = "blocked"
        safe_code = envelope.error.code if envelope.error is not None else "repair_agent_invalid_output"
        output_payload = None
    else:
        output = RepairInstructionContract.model_validate(envelope.output)
        actual_scope = output.repair_scope
        safe_code = None
        output_payload = output.model_dump(mode="json")
    return {
        "case": case.name,
        "expected_scope": case.expected_scope,
        "actual_scope": actual_scope,
        "matched": actual_scope == case.expected_scope,
        "safe_code": safe_code,
        "repair_instruction": output_payload,
    }


def _store_generated_result(*, case: AcceptanceCase, storage: InMemoryObjectStorage) -> AgentArtifactReference:
    """Store one generated result artifact in backend-owned temporary storage."""

    payload = case.generated_result_path.read_bytes()
    content_type = _content_type(case.generated_result_path)
    object_key = f"acceptance/repair-agent/{case.name}/generated_result.png"
    storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    return AgentArtifactReference(
        purpose="generated_result",
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(payload),
        sha256=sha256(payload).hexdigest(),
    )


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build one compact acceptance summary."""

    mismatches = [row["case"] for row in rows if row["matched"] is not True]
    false_local = [
        row["case"]
        for row in rows
        if row["expected_scope"] == "unsafe" and row["actual_scope"] == "local"
    ]
    false_unsafe = [
        row["case"]
        for row in rows
        if row["expected_scope"] == "local" and row["actual_scope"] == "unsafe"
    ]
    return {
        "total": len(rows),
        "matched": sum(1 for row in rows if row["matched"] is True),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "false_local_count": len(false_local),
        "false_unsafe_count": len(false_unsafe),
        "false_local_cases": false_local,
        "false_unsafe_cases": false_unsafe,
    }


def _content_type(path: Path) -> str:
    """Return one supported image content type for an acceptance asset."""

    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    raise ValueError(f"unsupported image type for acceptance asset: {path.name}")


def _output_path(path: Path | None) -> Path:
    """Resolve the JSONL output path."""

    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"repair_agent_live_acceptance_{timestamp}.jsonl"


def _load_settings(*, env_file: Path | None):
    """Load validated settings from env or one explicit env file."""

    if env_file is None:
        return load_settings()
    settings = Settings(_env_file=str(env_file), _env_file_encoding="utf-8")
    validate_settings(settings)
    return settings


def _write_jsonl(*, output_path: Path, rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    """Write acceptance rows and one summary line."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({"type": "case", **row}, ensure_ascii=False) + "\n")
        handle.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Run the Repair Agent live acceptance CLI."""

    args = _parser().parse_args(argv)
    try:
        cases = collect_acceptance_cases(args.assets_dir)
        settings = _load_settings(env_file=args.env_file)
        rows, summary = asyncio.run(_run_acceptance(cases=cases, settings=settings))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, rows=rows, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("repair_agent_live_acceptance_status=error")
        print(f"error={exc}")
        return 1

    print("repair_agent_live_acceptance_status=completed")
    print(f"output={output_path}")
    print(f"total={summary['total']}")
    print(f"matched={summary['matched']}")
    print(f"mismatch_count={summary['mismatch_count']}")
    print(f"false_local_count={summary['false_local_count']}")
    print(f"false_unsafe_count={summary['false_unsafe_count']}")
    if args.require_pass and summary["mismatch_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
