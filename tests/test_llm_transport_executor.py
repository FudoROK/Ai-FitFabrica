import json

from pydantic import BaseModel, ConfigDict

from src.llm.core.result import LLMResult as CoreLLMResult
from src.llm.core.types import LLMError
from src.llm.transport.executor import LLMTransportExecutor
from src.llm.transport.registry import register_schema


class LeadPatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    first_name: str = ""
    business_type: str = ""


class Payload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lead_patch: LeadPatch
    missing: list[str]
    confidence: float


class SequenceProvider:
    provider_name = "fake"

    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def generate(self, _request):
        result = self.results[self.calls]
        self.calls += 1
        return result


def test_transport_strict_success():
    register_schema("transport_test_strict", Payload)
    provider = SequenceProvider([
        CoreLLMResult(
            status="ok",
            structured_data={"lead_patch": {"first_name": "Ann", "business_type": "Shop"}, "missing": [], "confidence": 0.9},
        )
    ])
    executor = LLMTransportExecutor(provider)

    result = executor.run("transport_test_strict", "prompt")

    assert result.status == "success"
    assert result.attempt == "strict"
    assert result.data["lead_patch"]["first_name"] == "Ann"


def test_transport_strict_invalid_soft_success():
    register_schema("transport_test_soft", Payload)
    provider = SequenceProvider([
        CoreLLMResult(
            status="error",
            error=LLMError(type="invalid_output", message_redacted="bad schema", retriable=False),
        ),
        CoreLLMResult(
            status="ok",
            text='answer: ' + json.dumps({"lead_patch": {"first_name": "  Bob  ", "business_type": ""}, "missing": [], "confidence": 0.7}),
        ),
    ])
    executor = LLMTransportExecutor(provider)

    result = executor.run("transport_test_soft", "prompt")

    assert result.status == "partial"
    assert result.attempt == "soft"
    assert result.data["lead_patch"]["first_name"] == "Bob"
    assert "business_type" not in result.data["lead_patch"]


def test_transport_quarantine_when_both_fail():
    register_schema("transport_test_quarantine", Payload)
    provider = SequenceProvider([
        CoreLLMResult(status="error", error=LLMError(type="invalid_output", message_redacted="bad schema", retriable=False)),
        CoreLLMResult(status="ok", text="not json at all"),
    ])
    executor = LLMTransportExecutor(provider)

    result = executor.run("transport_test_quarantine", "prompt")

    assert result.status == "failed"
    assert result.attempt == "quarantine"
    assert result.raw_response == "not json at all"


def test_transport_sanitization_removes_empty_and_extra_keys():
    register_schema("transport_test_sanitize", Payload)
    provider = SequenceProvider([
        CoreLLMResult(
            status="ok",
            structured_data={
                "lead_patch": {"first_name": "  Alice  ", "business_type": "", "extra": "x"},
                "missing": [" ", "business_type"],
                "confidence": 0.5,
                "extra_top": "ignored",
            },
        )
    ])
    executor = LLMTransportExecutor(provider)

    result = executor.run("transport_test_sanitize", "prompt")

    assert result.status == "success"
    assert result.data["lead_patch"]["first_name"] == "Alice"
    assert "business_type" not in result.data["lead_patch"]
    assert "extra_top" not in result.data


def test_transport_profile_extract_keeps_empty_lead_patch_container():
    register_schema("profile_extract_task", Payload)
    provider = SequenceProvider([
        CoreLLMResult(
            status="ok",
            structured_data={
                "lead_patch": {"first_name": "", "business_type": ""},
                "missing": ["first_name"],
                "confidence": 0.3,
            },
        )
    ])
    executor = LLMTransportExecutor(provider)

    result = executor.run("profile_extract_task", "prompt")

    assert result.status == "success"
    assert "lead_patch" in result.data
    assert result.data["lead_patch"] == {}
