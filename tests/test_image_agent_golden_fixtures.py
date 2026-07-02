from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.adk_agents.human_identity_agent.contracts import HumanIdentityRequest


FIXTURE_ROOT = Path("tests/fixtures/agent_evaluations")


@pytest.mark.parametrize(
    "fixture_name",
    ("valid.json", "ambiguous.json"),
)
def test_human_identity_request_golden_fixtures_are_valid(fixture_name: str) -> None:
    payload = json.loads((FIXTURE_ROOT / "human_identity" / fixture_name).read_text(encoding="utf-8"))

    request = HumanIdentityRequest.model_validate(payload)

    assert request.human_photo_object_key


@pytest.mark.parametrize(
    "fixture_name",
    ("unsafe.json", "malformed.json"),
)
def test_human_identity_request_golden_fixtures_are_rejected(fixture_name: str) -> None:
    payload = json.loads((FIXTURE_ROOT / "human_identity" / fixture_name).read_text(encoding="utf-8"))

    with pytest.raises(ValidationError):
        HumanIdentityRequest.model_validate(payload)

