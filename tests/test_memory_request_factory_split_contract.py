from __future__ import annotations

import json
import pytest
from pydantic import ValidationError

from src.runtime_agents.memory_agent.memory_request_factory import build_memory_rolling_provider_request


def test_rolling_request_factory_preserves_split_runtime_payload_shape() -> None:
    request = build_memory_rolling_provider_request(
        {
            "model": "gemini-test",
            "prior_rolling_memory": {"rolling_summary_text": "prev"},
            "new_daily_summary": {"summary_text": "daily", "memory_day_key": "2026-01-01"},
            "daily_summary": {"summary_text": "legacy-should-be-ignored"},
            "rolling_summary": "legacy-should-be-ignored",
        }
    )

    payload = json.loads(request.input)
    assert payload == {
        "prior_rolling_memory": {"rolling_summary_text": "prev"},
        "new_daily_summary": {"summary_text": "daily", "memory_day_key": "2026-01-01"},
    }


def test_rolling_request_factory_uses_split_shape_defaults_when_payload_missing() -> None:
    with pytest.raises(ValidationError, match="prior_rolling_memory"):
        build_memory_rolling_provider_request({"model": "gemini-test"})
