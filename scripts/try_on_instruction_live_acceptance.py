"""Run Try-On Instruction live acceptance without image generation."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.adapters.agents.adk_agent_gateway import AdkAgentGateway
from src.adapters.agents.in_memory_repository import InMemoryAgentInvocationRepository
from src.adapters.agents.object_storage_artifact_resolver import ObjectStorageAgentArtifactResolver
from src.adapters.agents.try_on_instruction import TryOnInstructionAgentAdapter
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.domain.try_on import TryOnHumanIdentityAnalysis, TryOnHumanIdentityVerdict, TryOnWearControlSelection
from src.domain.try_on_analysis import (
    TryOnGarmentIdentityAnalysis,
    TryOnGarmentSlotIdentityAnalysis,
    TryOnMaterialTextureAnalysis,
)
from src.llm.provider_runtime import build_provider_runtime
from src.settings import Settings, load_settings, validate_settings
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundle
from src.use_cases.try_on.instruction_errors import TryOnInstructionFailure

REQUIRED_CASES = (
    "front_pose_coat_matte_woven",
    "front_pose_denim_jacket_textured",
)


@dataclass(frozen=True)
class AcceptanceCase:
    """One structured Try-On Instruction acceptance case."""

    name: str
    expected_decision: str
    analysis_bundle: TryOnAnalysisBundle
    wear_control_selections: list[TryOnWearControlSelection]


def expected_decision_for(case_name: str) -> str:
    """Return the expected backend decision for a named instruction case."""

    if case_name not in REQUIRED_CASES:
        raise ValueError(f"unknown Try-On Instruction acceptance case: {case_name}")
    return "allowed"


def build_acceptance_cases() -> list[AcceptanceCase]:
    """Build canonical structured upstream snapshots for live instruction acceptance."""

    cases = [
        AcceptanceCase(
            name="front_pose_coat_matte_woven",
            expected_decision=expected_decision_for("front_pose_coat_matte_woven"),
            analysis_bundle=_analysis_bundle(
                garment_type="coat",
                dominant_color="tan",
                silhouette_summary="Straight mid-thigh coat with pointed collar, button placket, and long sleeves.",
                preserved_details=[
                    "tan dominant color",
                    "pointed collar",
                    "front button placket",
                    "long sleeves",
                    "welt pockets",
                ],
                material_signals=["matte woven surface", "structured drape"],
                texture_signals=["fine visible weave", "low gloss finish"],
            ),
            wear_control_selections=[
                _wear_control_selection(
                    garment_type="coat",
                    control_code="open_front",
                    display_name="Open front",
                    instruction_template="Keep the coat open at the front so the base outfit remains visible.",
                )
            ],
        ),
        AcceptanceCase(
            name="front_pose_denim_jacket_textured",
            expected_decision=expected_decision_for("front_pose_denim_jacket_textured"),
            analysis_bundle=_analysis_bundle(
                garment_type="denim jacket",
                dominant_color="blue",
                silhouette_summary="Structured denim jacket with pointed collar, chest pockets, metal buttons, and contrast seams.",
                preserved_details=[
                    "blue denim color",
                    "pointed collar",
                    "two flap chest pockets",
                    "metal button front closure",
                    "contrast stitching",
                ],
                material_signals=["denim weave", "structured cotton-like surface"],
                texture_signals=["visible diagonal twill", "matte textured finish"],
            ),
            wear_control_selections=[
                _wear_control_selection(
                    garment_type="denim jacket",
                    control_code="buttoned_closed",
                    display_name="Buttoned closed",
                    instruction_template="Keep the denim jacket buttoned closed while preserving collar and pocket details.",
                )
            ],
        ),
    ]
    return sorted(cases, key=lambda item: item.name)


def _analysis_bundle(
    *,
    garment_type: str,
    dominant_color: str,
    silhouette_summary: str,
    preserved_details: list[str],
    material_signals: list[str],
    texture_signals: list[str],
) -> TryOnAnalysisBundle:
    """Create one approved analysis bundle with no image artifacts."""

    garment_identity = TryOnGarmentIdentityAnalysis(
        invocation_id="garment-approved-1",
        prompt_version="garment_identity.v1",
        contract_version="garment_identity.contract.v2",
        garment_type=garment_type,
        garment_count=1,
        target_garment_index=1,
        target_garment_description=f"{dominant_color} {garment_type}",
        garment_visibility="fully_visible",
        crop_quality="full_garment",
        try_on_garment_coverage="sufficient",
        product_card_coverage="sufficient",
        occlusion_risk="low",
        required_regions_missing=[],
        ambiguous_target=False,
        dominant_color=dominant_color,
        secondary_colors=[],
        silhouette_summary=silhouette_summary,
        preserved_details=preserved_details,
        visual_details=[
            {"detail_type": "other", "description": detail, "confidence": 0.9}
            for detail in preserved_details
        ],
        evidence=[
            {
                "source_type": "prior_agent_output",
                "source_ref": "garment_identity",
                "observation": f"Garment Identity approved one {garment_type}.",
                "confidence": 0.93,
            }
        ],
        confidence=0.93,
        limitations=[],
        uncertainty_level="low",
        unknowns=[],
    )

    return TryOnAnalysisBundle(
        human_identity=TryOnHumanIdentityAnalysis(
            invocation_id="human-approved-1",
            prompt_version="human_identity.v1",
            contract_version="human_identity.contract.v2",
            face_visibility="fully_visible",
            pose_summary="Single person in a clear front-facing full-body pose.",
            body_region_visibility=["face", "torso", "arms", "legs"],
            subject_count=1,
            crop_quality="full_body",
            try_on_body_coverage="sufficient",
            occlusion_risk="low",
            required_regions_missing=[],
            confidence=0.94,
            uncertainty_level="low",
            verdict=TryOnHumanIdentityVerdict.ALLOWED,
            preservation_targets=[
                {
                    "attribute_name": "face",
                    "preservation_reason": "Try-On generation must preserve identity.",
                },
                {
                    "attribute_name": "body_shape",
                    "preservation_reason": "Try-On generation must not reshape the person.",
                },
                {
                    "attribute_name": "pose",
                    "preservation_reason": "Try-On generation must preserve the source pose.",
                },
            ],
            evidence=[
                {
                    "source_type": "prior_agent_output",
                    "source_ref": "human_identity",
                    "observation": "Human Identity approved a single fully visible subject.",
                    "confidence": 0.94,
                }
            ],
        ),
        garment_identity=garment_identity,
        garment_slot_analyses=[
            TryOnGarmentSlotIdentityAnalysis(slot_role="garment_photo", analysis=garment_identity)
        ],
        material_texture=TryOnMaterialTextureAnalysis(
            invocation_id="material-approved-1",
            prompt_version="material_texture.v1",
            contract_version="material_texture.contract.v2",
            visible_material_signals=material_signals,
            texture_signals=texture_signals,
            evidence_note="Material / Texture analysis approved visible evidence without claiming exact fiber composition.",
            observations=[
                {"signal_type": "texture", "observation": signal, "confidence": 0.9}
                for signal in material_signals + texture_signals
            ],
            evidence=[
                {
                    "source_type": "prior_agent_output",
                    "source_ref": "material_texture",
                    "observation": "Material / Texture approved visible material cues only.",
                    "confidence": 0.91,
                }
            ],
            confidence=0.91,
            limitations=["Exact fiber composition is unknown without a trusted label or product data."],
            composition_status="unknown",
            uncertainty_level="low",
            alternative_interpretations=[],
        ),
    )


def _wear_control_selection(
    *,
    garment_type: str,
    control_code: str,
    display_name: str,
    instruction_template: str,
) -> TryOnWearControlSelection:
    """Create one backend-validated wear-control selection for live instruction acceptance."""
    return TryOnWearControlSelection(
        slot_role="garment_photo",
        garment_type=garment_type,
        requested_control_code=control_code,
        resolved_control_code=control_code,
        display_name=display_name,
        instruction_template=instruction_template,
        risk_level="low",
        resolved_by="acceptance_fixture",
    )


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description="Run Try-On Instruction live acceptance only.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output file. Defaults to output/try_on_instruction_live_acceptance_<timestamp>.jsonl.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file for Settings.")
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Exit non-zero when false_pass or false_reject is non-zero.",
    )
    return parser


async def _run_acceptance(*, cases: list[AcceptanceCase], settings) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Invoke only Try-On Instruction against structured upstream snapshots."""

    providers = build_provider_runtime(settings)
    if providers.agent_runtime is None:
        raise RuntimeError("Try-On Instruction live acceptance requires llm.provider=vertex with agent_runtime enabled.")
    gateway = AdkAgentGateway(
        agent_runtime=providers.agent_runtime,
        artifact_resolver=ObjectStorageAgentArtifactResolver(
            object_storage=InMemoryObjectStorage(),
            max_artifact_bytes=int(getattr(settings, "try_on_max_upload_bytes", 10 * 1024 * 1024)),
        ),
    )
    invocation_service = AgentInvocationService(
        gateway=gateway,
        repository=InMemoryAgentInvocationRepository(),
    )
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=invocation_service,
        minimum_confidence=float(getattr(settings, "try_on_instruction_minimum_confidence", 0.75)),
        timeout_seconds=float(getattr(settings, "try_on_instruction_timeout_seconds", 90.0)),
        preferred_model=getattr(settings, "try_on_instruction_preferred_model", None),
    )

    rows: list[dict[str, object]] = []
    for case in cases:
        rows.append(await _run_one_case(case=case, adapter=adapter))
    summary = _summarize(rows)
    return rows, summary


async def _run_one_case(*, case: AcceptanceCase, adapter: TryOnInstructionAgentAdapter) -> dict[str, object]:
    """Run one structured case and return a JSONL-safe acceptance row."""

    try:
        instruction = await adapter.create(
            job_id=f"instruction-live-{case.name}",
            analysis_bundle=case.analysis_bundle,
            wear_control_selections=case.wear_control_selections,
        )
        actual_decision = "allowed"
        safe_code = None
        instruction_payload: dict[str, object] | None = instruction.model_dump(mode="json")
    except TryOnInstructionFailure as exc:
        actual_decision = "blocked"
        safe_code = exc.safe_code
        instruction_payload = None
    matched = actual_decision == case.expected_decision
    return {
        "case": case.name,
        "expected_decision": case.expected_decision,
        "actual_decision": actual_decision,
        "matched": matched,
        "safe_code": safe_code,
        "instruction": instruction_payload,
    }


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build one compact acceptance summary."""

    false_pass = [
        row["case"]
        for row in rows
        if row["expected_decision"] == "blocked" and row["actual_decision"] == "allowed"
    ]
    false_reject = [
        row["case"]
        for row in rows
        if row["expected_decision"] == "allowed" and row["actual_decision"] == "blocked"
    ]
    return {
        "total": len(rows),
        "matched": sum(1 for row in rows if row["matched"] is True),
        "false_pass_count": len(false_pass),
        "false_reject_count": len(false_reject),
        "false_pass_cases": false_pass,
        "false_reject_cases": false_reject,
    }


def _output_path(path: Path | None) -> Path:
    """Resolve the JSONL output path."""

    if path is not None:
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"try_on_instruction_live_acceptance_{timestamp}.jsonl"


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
    """Run the Try-On Instruction live acceptance CLI."""

    args = _parser().parse_args(argv)
    try:
        cases = build_acceptance_cases()
        settings = _load_settings(env_file=args.env_file)
        rows, summary = asyncio.run(_run_acceptance(cases=cases, settings=settings))
        output_path = _output_path(args.output)
        _write_jsonl(output_path=output_path, rows=rows, summary=summary)
    except Exception as exc:  # noqa: BLE001
        print("try_on_instruction_live_acceptance_status=error")
        print(f"error={exc}")
        return 1

    print("try_on_instruction_live_acceptance_status=completed")
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
