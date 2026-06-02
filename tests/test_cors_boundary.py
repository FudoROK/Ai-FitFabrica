from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import configure_cors
from src.settings import load_settings


def test_configured_frontend_origin_can_preflight_try_on_upload(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:3000")
    load_settings.cache_clear()

    app = FastAPI()
    configure_cors(app, load_settings())

    response = TestClient(app).options(
        "/api/try-on/jobs",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_configured_frontend_origin_regex_can_preflight_try_on_upload(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.setenv("CORS_ALLOWED_ORIGIN_REGEX", r"^https://[a-z0-9-]+\.(web\.app|firebaseapp\.com)$")
    load_settings.cache_clear()

    app = FastAPI()
    configure_cors(app, load_settings())

    response = TestClient(app).options(
        "/api/try-on/jobs",
        headers={
            "Origin": "https://ai-fitfabrica.web.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ai-fitfabrica.web.app"
