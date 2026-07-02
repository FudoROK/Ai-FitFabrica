"""Run Garment Identity live acceptance without executing the full Try-On workflow."""

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
from src.adapters.agents.try_on_garment_identity_analysis import TryOnGarmentIdentityAnalysisAdapter
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.llm.provider_runtime import build_provider_runtime
from src.settings import Settings, load_settings, validate_settings
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.try_on.analysis_errors import GarmentIdentityAnalysisFailure

REQUIRED_CASES = (
    "coat_or_jacket.png",
    "cropped_garment.png",
    "dark_or_blurry_garment.png",
    "dress.png",
    "good_single_shirt.png",
    "logo_or_print_item.png",
    "multiple_garments.png",
    "not_garment.png",
    "pants_or_jeans.png",
    "patterned_item.png",
)

_EXPECTED_BLOCKED = {
    "cropped_garment.png",
    "dark_or_blurry_garment.png",
    "multiple_garments.png",
    "not_garment.png",
}


@dataclass(frozen=True)
class AcceptanceAsset:
    """One named Garment Identity acceptance asset."""

    path: Path
    expected_decision: str


def expected_decision_for(file_name: str) -> str:
    """Return the expected backend decision for a named acceptance image."""

    return "blocked" if file_name in _EXPECTED_BLOCKED else "allowed"


def collect_acceptance_assets(assets_dir: Path) -> list[AcceptanceAsset]:
    """Return the canonical 10-file Garment Identity acceptance dataset."""

    if not assets_dir.exists():
        raise ValueError(f"assets directory does not exist: {assets_dir}")
    missing = sorted(file_name for file_name in REQUIRED_CASES if not (assets_dir / file_name).is_file())
    if missing:
        raise ValueError(f"missing required garment acceptance files: {', '.join(missing)}")
    return [
        AcceptanceAsset(path=assets_dir / file_name, expected_decision=expected_decision_for(file_name))
        for file_name in sorted(REQUIRED_CASES)
    ]


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run Garment Identity live acceptance only.")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path("test-assets/garment-identity"),
        help="Directory containing the canonical 10-image Garment Identity dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/garment_identity_live_acceptance_<timestamp>.jsonl.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional env file for Settings.",
    )
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Exit non-zero when false_pass or false_reject is non-zero.",
    )
    return parser


async def _run_acceptance(*, assets: list[AcceptanceAsset], settings) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Invoke only Garment Identity against the supplied assets."""

    providers = build_provider_runtime(settings)
    if providers.agent_runtime is None:
        raise RuntimeError("Garment Identity live acceptance requires llm.provider=vertex with agent_runtime enabled.")
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
    adapter = TryOnGarmentIdentityAnalysisAdapter(
        invocation_service=invocation_service,
        minimum_confidence=float(getattr(settings, "try_on_garment_identity_minimum_confidence", 0.75)),
        timeout_seconds=float(getattr(settings, "try_on_garment_identity_timeout_seconds", 90.0)),
        preferred_model=getattr(settings, "try_on_garment_identity_preferred_model", None),
    )

    rows: list[dict[str, object]] = []
    for asset in assets:
        rows.append(await _run_one_asset(asset=asset, adapter=adapter, storage=storage))
    summary = _summarize(rows)
    return rows, summary


async def _run_one_asset(
    *,
    asset: AcceptanceAsset,
    adapter: TryOnGarmentIdentityAnalysisAdapter,
    storage: InMemoryObjectStorage,
) -> dict[str, object]:
    """Run one asset and return a JSONL-safe acceptance row."""

    payload = asset.path.read_bytes()
    content_type = _content_type(asset.path)
    digest = sha256(payload).hexdigest()
    object_key = f"acceptance/garment-identity/{asset.path.name}"
    storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    stored_input = TryOnStoredInput(
        role=TryOnUploadRole.GARMENT_PHOTO,
        storage_backend="in_memory",
        uri=f"memory://{object_key}",
        object_key=object_key,
        object_name=object_key,
        content_type=content_type,
        size_bytes=len(payload),
        sha256=digest,
    )
    try:
        analysis = await adapter.analyze(job_id=f"garment-live-{asset.path.stem}", stored_inputs=[stored_input])
        actual_decision = "allowed"
        safe_code = None
        analysis_payload: dict[str, object] | None = analysis.model_dump(mode="json")
    except GarmentIdentityAnalysisFailure as exc:
        actual_decision = "blocked"
        safe_code = exc.safe_code
        analysis_payload = None
    matched = actual_decision == asset.expected_decision
    return {
        "asset": asset.path.name,
        "expected_decision": asset.expected_decision,
        "actual_decision": actual_decision,
        "matched": matched,
        "safe_code": safe_code,
        "analysis": analysis_payload,
    }


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build one compact acceptance summary."""

    false_pass = [
        row["asset"]
        for row in rows
        if row["expected_decision"] == "blocked" and row["actual_decision"] == "allowed"
    ]
    false_reject = [
        row["asset"]
        for row in rows
        if row["expected_decision"] == "allowed" and row["actual_decision"] == "blocked"
    ]
    return {
        "total": len(rows),
        "matched": sum(1 for row in rows if row["matched"] is True),
        "false_pass_count": len(false_pass),
        "false_reject_count": len(false_reject),
        "false_pass_assets": false_pass,
        "false_reject_assets": false_reject,
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
    return Path("output") / f"garment_identity_live_acceptance_{timestamp}.jsonl"


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
    """Run the Garment Identity live acceptance CLI."""

    args = _parser().parse_args(argv)
    try:
        assets = collect_acceptance_assets(args.assets_dir)
        settings = _load_settings(env_file=args.env_file)
        rows, summary = asyncio.run(_run_acceptance(assets=assets, settings=settings))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, rows=rows, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print(f"garment_identity_live_acceptance_status=error")
        print(f"error={exc}")
        return 1

    print("garment_identity_live_acceptance_status=completed")
    print(f"output={output_path}")
    print(f"total={summary['total']}")
    print(f"matched={summary['matched']}")
    print(f"false_pass_count={summary['false_pass_count']}")
    print(f"false_reject_count={summary['false_reject_count']}")
    if args.require_pass and (summary["false_pass_count"] or summary["false_reject_count"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
