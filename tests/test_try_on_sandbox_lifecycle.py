from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_try_on_missing_files_returns_typed_error():
    response = client.post("/api/try-on/jobs", files={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "missing_required_file"
    assert body["error"]["details"]["fields"] == ["human_photo", "garment_photo"]


def test_try_on_rejects_unsupported_content_type():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.txt", b"hello", "text/plain"),
            "garment_photo": ("garment.png", b"fake-image", "image/png"),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "unsupported_content_type"
    assert body["error"]["details"]["field"] == "human_photo"
