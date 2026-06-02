import logging

import pytest

from src.settings import load_settings
from src.utils.log_redaction import RedactingLogFilter


REQUIRED_ENV_KEYS = [
    "GCP_PROJECT_ID",
    "PUBSUB_TOPIC_NAME",
    "VERTEX_PROJECT",
]


def _set_minimal_valid_vertex_env(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "proj")
    monkeypatch.setenv("PUBSUB_TOPIC_NAME", "topic")
    monkeypatch.setenv("LLM_PROVIDER", "vertex")
    monkeypatch.setenv("VERTEX_PROJECT", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setenv("VERTEX_AGENT_RESOURCE", "projects/547855929194/locations/us-central1/reasoningEngines/123267348101595136")


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    load_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "test")
    for key in REQUIRED_ENV_KEYS + ["LLM_PROVIDER", "VERTEX_PROJECT", "VERTEX_LOCATION", "VERTEX_AGENT_RESOURCE", "ENV", "DEBUG", "LOG_LEVEL", "CRM_PROVIDER", "CALENDAR_PROVIDER", "MESSAGING_PROVIDER", "KNOWLEDGE_PROVIDER", "HUBSPOT_SYNC_ENABLED"]:
        monkeypatch.delenv(key, raising=False)
    yield
    load_settings.cache_clear()


def test_load_settings_fails_without_required_vertex_agent_resource(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.delenv("VERTEX_AGENT_RESOURCE", raising=False)

    with pytest.raises(ValueError) as exc:
        load_settings()

    assert "VERTEX_AGENT_RESOURCE" in str(exc.value)


def test_load_settings_vertex_mode(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)

    settings = load_settings()

    assert settings.llm.provider == "vertex"
    assert settings.llm.model


def test_load_settings_fake_mode_does_not_require_vertex_project(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("VERTEX_PROJECT", raising=False)

    settings = load_settings()

    assert settings.llm.provider == "fake"



def test_load_settings_gemini_structured_mode_requires_memory_runtime_resource_when_memory_summary_enabled(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini_structured")
    monkeypatch.delenv("VERTEX_AGENT_RESOURCE", raising=False)
    monkeypatch.delenv("VERTEX_MEMORY_DAILY_AGENT_RESOURCE", raising=False)
    monkeypatch.delenv("VERTEX_MEMORY_ROLLING_AGENT_RESOURCE", raising=False)

    with pytest.raises(ValueError) as exc:
        load_settings()

    assert "VERTEX_MEMORY_DAILY_AGENT_RESOURCE and VERTEX_MEMORY_ROLLING_AGENT_RESOURCE" in str(exc.value)


def test_load_settings_gemini_structured_mode_allows_missing_vertex_agent_resource_when_memory_summary_disabled(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini_structured")
    monkeypatch.setenv("MEMORY_SUMMARY_ENABLED", "false")
    monkeypatch.delenv("VERTEX_AGENT_RESOURCE", raising=False)

    settings = load_settings()

    assert settings.llm.provider == "gemini_structured"


def test_load_settings_gemini_structured_requires_vertex_project(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini_structured")
    monkeypatch.delenv("VERTEX_PROJECT", raising=False)

    with pytest.raises(ValueError) as exc:
        load_settings()

    assert "VERTEX_PROJECT" in str(exc.value)


def test_load_settings_sets_httpx_warning_in_prod(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    load_settings()

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING


def test_load_settings_allows_httpx_info_in_dev(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    load_settings()

    assert logging.getLogger("httpx").level == logging.INFO
    assert logging.getLogger("httpcore").level == logging.INFO


def test_load_settings_does_not_require_hubspot_token_when_crm_provider_none(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("CRM_PROVIDER", "none")
    monkeypatch.delenv("HUBSPOT_PRIVATE_APP_TOKEN", raising=False)

    settings = load_settings()

    assert settings.crm_provider == "none"


def test_load_settings_uses_web_first_no_messaging_default(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("MESSAGING_PROVIDER", "none")

    settings = load_settings()

    assert settings.messaging_provider == "none"


def test_load_settings_rejects_legacy_telegram_messaging_provider(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    monkeypatch.setenv("MESSAGING_PROVIDER", "telegram")

    with pytest.raises(ValueError) as exc:
        load_settings()

    assert "MESSAGING_PROVIDER" in str(exc.value)


def test_load_settings_installs_redaction_enforcement_on_root_pipeline(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)
    root = logging.getLogger()
    temp_handler = logging.StreamHandler()
    root.addHandler(temp_handler)
    try:
        load_settings()
        assert any(isinstance(flt, RedactingLogFilter) for flt in root.filters)
        assert any(isinstance(flt, RedactingLogFilter) for flt in temp_handler.filters)
    finally:
        root.removeHandler(temp_handler)


def test_load_settings_configures_cloud_json_formatter(monkeypatch):
    _set_minimal_valid_vertex_env(monkeypatch)

    load_settings()

    root = logging.getLogger()
    assert root.handlers
    assert any(handler.formatter.__class__.__name__ == "CloudJsonFormatter" for handler in root.handlers)


def test_cloud_json_formatter_serializes_extra_fields(monkeypatch):
    import json

    from src.utils.structured_logging import CloudJsonFormatter

    _set_minimal_valid_vertex_env(monkeypatch)

    formatter = CloudJsonFormatter()
    record = logging.getLogger("test").makeRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "MEMORY_PARSER_INPUT_SHAPE",
        args=(),
        exc_info=None,
        extra={
            "top_level_keys": ["a", "b"],
            "top_level_key_count": 2,
            "nested_blocks": ["facts"],
            "shape_fingerprint": "abc",
            "lead_id": "lead-1",
            "correlation_id": "corr-1",
        },
    )

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "MEMORY_PARSER_INPUT_SHAPE"
    assert payload["top_level_keys"] == ["a", "b"]
    assert payload["top_level_key_count"] == 2
    assert payload["nested_blocks"] == ["facts"]
    assert payload["shape_fingerprint"] == "abc"
    assert payload["lead_id"] == "lead-1"
    assert payload["correlation_id"] == "corr-1"

