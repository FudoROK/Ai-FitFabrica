"""Run Quality Verifier live visual acceptance without Try-On generation."""

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
from src.adk_agents.quality_verifier_agent.contracts import QualityVerifierDecisionContract, QualityVerifierRequest
from src.adk_agents.quality_verifier_agent.deploy_config import QualityVerifierAgentDeployConfig
from src.adk_agents.quality_verifier_agent.prompt_config import QUALITY_VERIFIER_INSTRUCTION
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.llm.provider_runtime import build_provider_runtime
from src.settings import Settings, load_settings, validate_settings
from src.use_cases.agents.invocation_service import AgentInvocationService

REQUIRED_FILES = (
    "garment_source.png",
    "generated_result.png",
    "human_source.png",
)

REQUIRED_CASES = (
    "body_pose_changed",
    "face_changed",
    "good_generated_result",
    "minor_background_artifact",
    "minor_color_shift",
    "missing_key_garment_detail",
    "severe_anatomy_artifact",
    "wrong_garment",
)

_EXPECTED_DECISIONS = {
    "good_generated_result": "pass",
    "minor_background_artifact": "repair_recommended",
    "minor_color_shift": "reject",
    "face_changed": "reject",
    "body_pose_changed": "reject",
    "wrong_garment": "reject",
    "missing_key_garment_detail": "reject",
    "severe_anatomy_artifact": "reject",
}

_ACCEPTABLE_DECISIONS = {
    "good_generated_result": frozenset({"pass"}),
    "minor_background_artifact": frozenset({"repair_recommended"}),
    "minor_color_shift": frozenset({"repair_recommended", "reject"}),
    "face_changed": frozenset({"reject"}),
    "body_pose_changed": frozenset({"reject"}),
    "wrong_garment": frozenset({"reject"}),
    "missing_key_garment_detail": frozenset({"reject"}),
    "severe_anatomy_artifact": frozenset({"reject"}),
}

_CASE_WEAR_CONTROL_CONSTRAINTS = {
    case_name: (
        "Selected wear control: buttoned_closed is explicitly approved for this case. "
        "The generated garment may be worn buttoned or closed over the original visible base layer. "
        "Do not reject the buttoned front or normal neckline/base-layer visibility by itself; only report "
        "defect_type wear_control when the result visibly contradicts buttoned_closed."
    )
    for case_name in REQUIRED_CASES
}


@dataclass(frozen=True)
class AcceptanceCase:
    """One named Quality Verifier visual acceptance case."""

    name: str
    path: Path
    expected_decision: str
    files: dict[str, Path]


def expected_decision_for(case_name: str) -> str:
    """Return the expected backend decision for a named visual quality case."""

    try:
        return _EXPECTED_DECISIONS[case_name]
    except KeyError as exc:
        raise ValueError(f"unknown Quality Verifier acceptance case: {case_name}") from exc


def acceptable_decisions_for(case_name: str) -> frozenset[str]:
    """Return all safe verifier decisions for a named visual quality case."""

    try:
        return _ACCEPTABLE_DECISIONS[case_name]
    except KeyError as exc:
        raise ValueError(f"unknown Quality Verifier acceptance case: {case_name}") from exc


def collect_acceptance_cases(assets_dir: Path) -> list[AcceptanceCase]:
    """Return the canonical 8-case Quality Verifier visual acceptance dataset."""

    if not assets_dir.exists():
        raise ValueError(f"assets directory does not exist: {assets_dir}")
    missing_cases = sorted(case_name for case_name in REQUIRED_CASES if not (assets_dir / case_name).is_dir())
    if missing_cases:
        raise ValueError(f"missing required quality verifier case directories: {', '.join(missing_cases)}")
    cases: list[AcceptanceCase] = []
    for case_name in sorted(REQUIRED_CASES):
        case_dir = assets_dir / case_name
        missing_files = sorted(file_name for file_name in REQUIRED_FILES if not (case_dir / file_name).is_file())
        if missing_files:
            raise ValueError(f"missing files for {case_name}: {', '.join(missing_files)}")
        cases.append(
            AcceptanceCase(
                name=case_name,
                path=case_dir,
                expected_decision=expected_decision_for(case_name),
                files={file_name: case_dir / file_name for file_name in REQUIRED_FILES},
            )
        )
    return cases


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run Quality Verifier live visual acceptance only.")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path("test-assets/quality-verifier"),
        help="Directory containing the canonical 8-case Quality Verifier dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/quality_verifier_live_acceptance_<timestamp>.jsonl.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Exit non-zero when false_pass, false_repair, or false_reject is non-zero.",
    )
    return parser


async def _run_acceptance(*, cases: list[AcceptanceCase], settings) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Invoke only Quality Verifier against the supplied visual cases."""

    providers = build_provider_runtime(settings)
    if providers.agent_runtime is None:
        raise RuntimeError("Quality Verifier live acceptance requires llm.provider=vertex with agent_runtime enabled.")
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
    config = QualityVerifierAgentDeployConfig()
    preferred_model = getattr(settings, "try_on_quality_verifier_preferred_model", None) or config.model
    timeout_seconds = float(getattr(settings, "try_on_quality_verifier_timeout_seconds", 120.0))

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
    config: QualityVerifierAgentDeployConfig,
    preferred_model: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Run one visual quality case and return a JSONL-safe acceptance row."""

    artifact_refs = [_store_artifact(case=case, file_name=file_name, storage=storage) for file_name in REQUIRED_FILES]
    request_payload = QualityVerifierRequest(
        human_photo_object_key=f"acceptance/quality-verifier/{case.name}/human_source.png",
        garment_photo_object_key=f"acceptance/quality-verifier/{case.name}/garment_source.png",
        generated_image_object_key=f"acceptance/quality-verifier/{case.name}/generated_result.png",
        approved_constraints=quality_verifier_approved_constraints(case),
    )
    envelope = await invocation_service.invoke(
        request=AgentInvocationRequest(
            agent_name=config.name,
            prompt_version=config.prompt_version,
            contract_version=config.contract_version,
            trace_id=f"quality-live-{case.name}",
            prompt=QUALITY_VERIFIER_INSTRUCTION,
            input_payload=request_payload.model_dump(mode="json"),
            artifact_references=artifact_refs,
            response_schema=QualityVerifierDecisionContract.model_json_schema(),
            timeout_seconds=timeout_seconds,
            preferred_model=preferred_model,
        ),
        output_contract=QualityVerifierDecisionContract,
    )
    if (
        envelope.status != AgentRuntimeStatus.SUCCEEDED
        or envelope.validation_status != AgentValidationStatus.PASSED
        or envelope.output is None
    ):
        actual_decision = "blocked"
        safe_code = envelope.error.code if envelope.error is not None else "quality_verifier_invalid_output"
        output_payload = None
    else:
        output = QualityVerifierDecisionContract.model_validate(envelope.output)
        actual_decision = output.verdict.value
        safe_code = None
        output_payload = output.model_dump(mode="json")
    acceptable_decisions = acceptable_decisions_for(case.name)
    return {
        "case": case.name,
        "expected_decision": case.expected_decision,
        "acceptable_decisions": sorted(acceptable_decisions),
        "actual_decision": actual_decision,
        "matched": actual_decision in acceptable_decisions,
        "safe_code": safe_code,
        "decision": output_payload,
    }


def _store_artifact(*, case: AcceptanceCase, file_name: str, storage: InMemoryObjectStorage) -> AgentArtifactReference:
    """Store one case artifact in backend-owned temporary storage."""

    path = case.files[file_name]
    payload = path.read_bytes()
    content_type = _content_type(path)
    object_key = f"acceptance/quality-verifier/{case.name}/{file_name}"
    storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    return AgentArtifactReference(
        purpose=file_name.removesuffix(".png"),
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(payload),
        sha256=sha256(payload).hexdigest(),
    )


def quality_verifier_approved_constraints(case: AcceptanceCase) -> list[str]:
    """Return visible constraints for the verifier to check."""

    base = [
        "Preserve the source person's face and identity.",
        "Preserve the source body shape, pose, and proportions.",
        "Apply only the approved source garment.",
        "Preserve garment color, silhouette, key details, and visible texture.",
        (
            "Do not reject normal collar opening, neckline, or visible skin/base layer at the neck unless an "
            "unapproved extra garment is clearly visible and materially contradicts the source garment."
        ),
        wear_control_constraint_for(case.name),
        (
            "Selected wear control: preserve the visible backend-approved way the garment is worn in this case; "
            "score wear_control_match and report defect_type wear_control for visible violations."
        ),
    ]
    if case.expected_decision == "repair_recommended":
        return base + ["Local visual defects may be repairable if identity, pose, and garment are otherwise preserved."]
    return base


def wear_control_constraint_for(case_name: str) -> str:
    """Return the explicit selected wear-control instruction for a visual case."""

    try:
        return _CASE_WEAR_CONTROL_CONSTRAINTS[case_name]
    except KeyError as exc:
        raise ValueError(f"unknown Quality Verifier acceptance case: {case_name}") from exc


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build one compact acceptance summary."""

    mismatches = [row["case"] for row in rows if row["matched"] is not True]
    false_pass = [
        row["case"]
        for row in rows
        if row["expected_decision"] != "pass" and row["actual_decision"] == "pass"
    ]
    false_repair = [
        row["case"]
        for row in rows
        if row["actual_decision"] == "repair_recommended"
        and row["actual_decision"] not in set(row["acceptable_decisions"])
    ]
    false_reject = [
        row["case"]
        for row in rows
        if row["actual_decision"] == "reject" and row["actual_decision"] not in set(row["acceptable_decisions"])
    ]
    return {
        "total": len(rows),
        "matched": sum(1 for row in rows if row["matched"] is True),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "false_pass_count": len(false_pass),
        "false_repair_count": len(false_repair),
        "false_reject_count": len(false_reject),
        "false_pass_cases": false_pass,
        "false_repair_cases": false_repair,
        "false_reject_cases": false_reject,
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
    return Path("output") / f"quality_verifier_live_acceptance_{timestamp}.jsonl"


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
    """Run the Quality Verifier live acceptance CLI."""

    args = _parser().parse_args(argv)
    try:
        cases = collect_acceptance_cases(args.assets_dir)
        settings = _load_settings(env_file=args.env_file)
        rows, summary = asyncio.run(_run_acceptance(cases=cases, settings=settings))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, rows=rows, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("quality_verifier_live_acceptance_status=error")
        print(f"error={exc}")
        return 1

    print("quality_verifier_live_acceptance_status=completed")
    print(f"output={output_path}")
    print(f"total={summary['total']}")
    print(f"matched={summary['matched']}")
    print(f"mismatch_count={summary['mismatch_count']}")
    print(f"false_pass_count={summary['false_pass_count']}")
    print(f"false_repair_count={summary['false_repair_count']}")
    print(f"false_reject_count={summary['false_reject_count']}")
    if args.require_pass and summary["mismatch_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
