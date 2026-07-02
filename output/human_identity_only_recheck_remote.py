
import asyncio
import json
import time
from src.settings import Settings
from src.entrypoints.runtime_dependencies import try_on_runtime_dependencies

ITEMS = [{"file": "blurry_dark.jpg", "job_id": "try_on_21779db9d9b541d7a983dde6355ff728"}, {"file": "cropped_face_only.jpg", "job_id": "try_on_b67af7d176b64d62b0e9992b938bd701"}, {"file": "face_hidden.jpg", "job_id": "try_on_c58f1d8b513e4e1e831df63d475922db"}, {"file": "good_front.jpg", "job_id": "try_on_c8b1d1401aab4ee29bd97945305a582b"}, {"file": "multiple_people.jpg", "job_id": "try_on_b7b55791c96240329f9021e065c590c4"}, {"file": "multiple_people_masks.jpg", "job_id": "try_on_e76bff9a50c542fd98ec64ec5e71a1a9"}, {"file": "not_human.jpg", "job_id": "try_on_f54ab6cb560f476f9292716d19765359"}, {"file": "side_pose.jpg", "job_id": "try_on_c79d620628e04bd08752cd5ee107b1d3"}]

async def main():
    settings = Settings()
    runtime = try_on_runtime_dependencies(settings)
    out = []
    for item in ITEMS:
        job = await runtime.job_repository.get(item["job_id"])
        row = dict(item)
        if job is None:
            row["error"] = "job_not_found"
            out.append(row)
            continue
        try:
            analysis = await runtime.human_identity_analyzer.analyze(
                job_id=item["job_id"] + "_human_only",
                stored_inputs=job.stored_inputs,
            )
            row.update({
                "verdict": analysis.verdict.value,
                "confidence": analysis.confidence,
                "uncertainty_level": analysis.uncertainty_level,
                "face_visibility": analysis.face_visibility,
                "subject_count": analysis.subject_count,
                "crop_quality": analysis.crop_quality,
                "try_on_body_coverage": analysis.try_on_body_coverage,
                "occlusion_risk": analysis.occlusion_risk,
                "required_regions_missing": analysis.required_regions_missing,
                "rejection_reasons": analysis.rejection_reasons,
            })
        except Exception as exc:
            row["error"] = type(exc).__name__
            row["error_message"] = str(exc)
        out.append(row)
        time.sleep(20)
    print(json.dumps(out, ensure_ascii=False, indent=2))

asyncio.run(main())
