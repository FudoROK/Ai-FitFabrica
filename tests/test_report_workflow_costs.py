from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_report_workflow_costs_outputs_json_from_offline_input(tmp_path: Path) -> None:
    input_path = tmp_path / "cost_records.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "job_id": "try_on_1",
                    "workflow_type": "try_on",
                    "status": "completed",
                    "credits_charged": 12,
                    "agent_invocations": [
                        {
                            "agent_name": "human_identity_agent",
                            "provider": "gemini",
                            "model": "gemini-2.5-flash",
                            "estimated_provider_cost_usd": "0.0055",
                            "estimated_internal_cost_usd": "0.0066",
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/report_workflow_costs.py",
            "--input-json",
            str(input_path),
            "--workflow",
            "try_on",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["total_jobs"] == 1
    assert payload["successful_jobs"] == 1
    assert payload["provider_cost_by_agent"]["human_identity_agent"] == "0.005500"


def test_report_workflow_costs_outputs_markdown_from_offline_input(tmp_path: Path) -> None:
    input_path = tmp_path / "cost_records.json"
    input_path.write_text("[]", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/report_workflow_costs.py", "--input-json", str(input_path), "--format", "markdown"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "| metric | value |" in result.stdout
