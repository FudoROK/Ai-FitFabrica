"""Local-only FastAPI server for browser acceptance of the Try-On UI flow."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI FitFabrica Try-On UI Acceptance Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

_jobs: dict[str, dict[str, object]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
async def health() -> dict[str, str]:
    """Return local acceptance server health."""
    return {"status": "ok"}


@app.get("/api/workspace/bootstrap")
async def workspace_bootstrap() -> dict[str, object]:
    """Return the minimal workspace bootstrap contract required by the shell."""
    return {
        "user": {"first_name": "Acceptance", "full_name": "Acceptance User"},
        "credit_owner": {"owner_id": "public-person", "owner_type": "person"},
        "credits": {"balance": 100, "currency": "credits", "low_balance_threshold": 10, "billing_enabled": False},
        "workflow_costs": {"product_card": 0},
        "business_profile": {"exists": True, "display_name": "Acceptance", "channels": []},
        "integrations": {"has_connected_store": False, "connected_channels": []},
        "capabilities": ["try_on_create"],
        "quick_actions": [],
        "recent_jobs": [],
    }


@app.post("/api/try-on/jobs", status_code=202)
async def create_try_on_job(
    human_photo: UploadFile | None = File(default=None),
    garment_photo: UploadFile | None = File(default=None),
    upper_garment_photo: UploadFile | None = File(default=None),
    lower_garment_photo: UploadFile | None = File(default=None),
    outerwear_garment_photo: UploadFile | None = File(default=None),
    full_body_garment_photo: UploadFile | None = File(default=None),
    sandbox_lifecycle_mode: str = Form(default="complete"),
) -> dict[str, object]:
    """Create an immediately analyzed local Try-On job."""
    job_id = f"try_on_{uuid4().hex}"
    uploads = [
        ("human_photo", human_photo),
        ("garment_photo", garment_photo),
        ("upper_garment_photo", upper_garment_photo),
        ("lower_garment_photo", lower_garment_photo),
        ("outerwear_garment_photo", outerwear_garment_photo),
        ("full_body_garment_photo", full_body_garment_photo),
    ]
    metadata = [
        {
            "role": role,
            "filename": upload.filename or f"{role}.png",
            "content_type": upload.content_type or "image/png",
            "size_bytes": 10,
            "sha256": "a" * 64,
        }
        for role, upload in uploads
        if upload is not None
    ]
    status_history = [
        {"status": "accepted", "stage": "accepted", "message": "Job accepted.", "occurred_at": _now()},
        {
            "status": "analyzing_human",
            "stage": "human_identity_analysis",
            "message": "Analyzing human preservation constraints.",
            "occurred_at": _now(),
        },
        {
            "status": "analysis_ready",
            "stage": "analysis_ready",
            "message": "Input analysis is ready for user wear-control selection.",
            "occurred_at": _now(),
        },
    ]
    _jobs[job_id] = {
        "status": "analysis_ready" if sandbox_lifecycle_mode == "analysis_only" else "completed",
        "input_metadata": metadata,
        "status_history": status_history,
        "selections": [],
    }
    return {
        "job_id": job_id,
        "workflow_type": "try_on",
        "status": "accepted",
        "input_metadata": metadata,
        "status_url": f"/api/jobs/{job_id}/status",
        "result_url": f"/api/jobs/{job_id}/result",
    }


@app.get("/api/jobs/{job_id}/status")
async def job_status(job_id: str) -> dict[str, object]:
    """Return local job status."""
    job = _jobs[job_id]
    return {
        "job_id": job_id,
        "workflow_type": "try_on",
        "status": job["status"],
        "status_history": job["status_history"],
        "cost_events": [
            {
                "event_type": "try_on_sandbox_generation",
                "estimated_units": 0,
                "charge_status": "not_charged",
                "charged_credits": 0,
                "occurred_at": _now(),
            }
        ],
    }


@app.get("/api/jobs/{job_id}/pre-generation-analysis")
async def pre_generation_analysis(job_id: str) -> dict[str, object]:
    """Return deterministic slot analysis and one approved wear control."""
    job = _jobs[job_id]
    garment_roles = [item["role"] for item in job["input_metadata"] if item["role"] != "human_photo"]
    return {
        "job_id": job_id,
        "workflow_type": "try_on",
        "status": "analysis_ready",
        "slots": [
            {
                "slot_role": role,
                "garment_type": "test garment",
                "taxonomy_item_code": "test_garment",
                "selected_control_code": "auto",
                "controls": [
                    {
                        "control_code": "relaxed_drape",
                        "display_name": "Relaxed drape",
                        "description": "Local acceptance wear-control option.",
                        "instruction_template": "Keep the test garment relaxed and untucked over the base outfit.",
                        "risk_level": "low",
                        "default_for_auto": True,
                    }
                ],
            }
            for role in garment_roles
        ],
        "generate_url": f"/api/jobs/{job_id}/generate",
    }


@app.put("/api/jobs/{job_id}/wear-controls")
async def save_wear_controls(job_id: str, payload: dict[str, object]) -> dict[str, object]:
    """Persist local wear-control selections."""
    selections = payload.get("selections", [])
    _jobs[job_id]["selections"] = selections
    return {"job_id": job_id, "status": "analysis_ready", "selections": selections}


@app.post("/api/jobs/{job_id}/generate", status_code=202)
async def generate(job_id: str) -> dict[str, object]:
    """Complete local generation after wear-control selection."""
    job = _jobs[job_id]
    job["status"] = "completed"
    job["status_history"] = [
        *job["status_history"],
        {"status": "generating", "stage": "sandbox_generation", "message": "Generating sandbox result.", "occurred_at": _now()},
        {"status": "quality_checking", "stage": "quality_check", "message": "Checking generated result quality.", "occurred_at": _now()},
        {"status": "completed", "stage": "completed", "message": "Try-On job completed.", "occurred_at": _now()},
    ]
    return {
        "job_id": job_id,
        "workflow_type": "try_on",
        "status": "analysis_ready",
        "input_metadata": job["input_metadata"],
        "status_url": f"/api/jobs/{job_id}/status",
        "result_url": f"/api/jobs/{job_id}/result",
    }


@app.get("/api/jobs/{job_id}/result")
async def result(job_id: str) -> dict[str, object]:
    """Return local completed Try-On result."""
    job = _jobs[job_id]
    if job["status"] != "completed":
        return {
            "status": "not_ready",
            "job_id": job_id,
            "workflow_type": "try_on",
            "current_status": job["status"],
            "status_url": f"/api/jobs/{job_id}/status",
        }
    return {
        "status": "completed",
        "job_id": job_id,
        "workflow_type": "try_on",
        "result": {
            "job_id": job_id,
            "workflow_type": "try_on",
            "result_image": {
                "kind": "sandbox_placeholder",
                "url": "/images/shared/try-on-sandbox-result.svg",
                "alt": "Sandbox Try-On result preview",
            },
            "quality_report": {
                "verdict": "pass",
                "confidence": 1.0,
                "checks": [],
                "limitations": ["Local UI acceptance server."],
            },
            "stylist_note": "Local UI acceptance completed.",
            "input_metadata": job["input_metadata"],
            "completed_at": _now(),
        },
    }
