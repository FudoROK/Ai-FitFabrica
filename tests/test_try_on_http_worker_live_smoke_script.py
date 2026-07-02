from __future__ import annotations

import json


class _Response:
    def __init__(self, status_code: int, payload: dict[str, object]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(self.text)


class _Client:
    def __init__(self, *args, **kwargs) -> None:
        self.status_calls = 0
        self.expected_lifecycle_mode = "complete"

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def post(self, url: str, *, files: dict[str, object], data: dict[str, str]):
        assert url.endswith("/api/try-on/jobs")
        assert "human_photo" in files
        assert "garment_photo" in files
        assert data["sandbox_lifecycle_mode"] == self.expected_lifecycle_mode
        return _Response(
            202,
            {
                "job_id": "try_on_http_1",
                "status_url": "/api/jobs/try_on_http_1/status",
                "result_url": "/api/jobs/try_on_http_1/result",
            },
        )

    def get(self, url: str):
        if url.endswith("/status"):
            self.status_calls += 1
            return _Response(
                200,
                {
                    "job_id": "try_on_http_1",
                    "status": "completed" if self.status_calls > 1 else "generating",
                },
            )
        return _Response(
            200,
            {
                "status": "completed",
                "job_id": "try_on_http_1",
                "result": {
                    "result_image": {"kind": "generated_artifact", "url": "s3://bucket/result.png"},
                    "quality_report": {"verdict": "pass", "confidence": 0.86, "checks": [], "limitations": []},
                },
            },
        )


def test_try_on_http_worker_smoke_polls_until_completed(tmp_path, monkeypatch) -> None:
    from scripts import try_on_http_worker_live_smoke

    human = tmp_path / "human.png"
    garment = tmp_path / "garment.png"
    output = tmp_path / "http-smoke.jsonl"
    human.write_bytes(b"human")
    garment.write_bytes(b"garment")
    monkeypatch.setattr(try_on_http_worker_live_smoke.httpx, "Client", _Client)
    monkeypatch.setattr(try_on_http_worker_live_smoke.time, "sleep", lambda _seconds: None)

    exit_code = try_on_http_worker_live_smoke.main(
        [
            "--base-url",
            "http://127.0.0.1:8080",
            "--human",
            str(human),
            "--garment",
            str(garment),
            "--output",
            str(output),
            "--require-pass",
        ]
    )

    assert exit_code == 0
    rows = output.read_text(encoding="utf-8").splitlines()
    assert '"type": "summary"' in rows[-1]
    assert '"passed": true' in rows[-1]
    assert '"final_status": "completed"' in rows[-1]
    assert '"quality_verdict": "pass"' in rows[-1]


def test_try_on_http_worker_smoke_can_request_repair_acceptance_mode(tmp_path, monkeypatch) -> None:
    from scripts import try_on_http_worker_live_smoke

    human = tmp_path / "human.png"
    garment = tmp_path / "garment.png"
    output = tmp_path / "http-smoke.jsonl"
    human.write_bytes(b"human")
    garment.write_bytes(b"garment")

    class _RepairAcceptanceClient(_Client):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.expected_lifecycle_mode = "repair_acceptance"

    monkeypatch.setattr(try_on_http_worker_live_smoke.httpx, "Client", _RepairAcceptanceClient)
    monkeypatch.setattr(try_on_http_worker_live_smoke.time, "sleep", lambda _seconds: None)

    exit_code = try_on_http_worker_live_smoke.main(
        [
            "--base-url",
            "http://127.0.0.1:8080",
            "--human",
            str(human),
            "--garment",
            str(garment),
            "--sandbox-lifecycle-mode",
            "repair_acceptance",
            "--output",
            str(output),
            "--require-pass",
        ]
    )

    assert exit_code == 0
