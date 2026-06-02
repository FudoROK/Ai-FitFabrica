from src.llm.core.request import LLMRequest
from src.llm.providers.fake_provider import FakeProvider


def _request(*, schema=None, task="dialog_reply_task") -> LLMRequest:
    return LLMRequest(
        task=task,
        input="hello",
        structured_output={"schema": schema} if schema else None,
        metadata={},
        max_retries=1,
    )


def test_fake_provider_ok_text_and_json():
    provider = FakeProvider(task_outputs={"dialog_reply_task": {"text": "ok", "json": {"answer": "yes"}}})

    result = provider.generate(_request())

    assert result.status == "ok"
    assert result.text == "ok"
    assert result.structured_data == {"answer": "yes"}
    assert result.error is None


def test_fake_provider_invalid_output_when_schema_mismatch():
    provider = FakeProvider(task_outputs={"dialog_reply_task": {"json": {"answer": 123}}})
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "string"}},
    }

    result = provider.generate(_request(schema=schema))

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "invalid_output"


def test_fake_provider_rate_limited_failure():
    provider = FakeProvider(failing_tasks={"dialog_reply_task": "rate_limited"})

    result = provider.generate(_request())

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "rate_limited"
    assert result.error.retriable is True


def test_fake_provider_timeout_failure():
    provider = FakeProvider(failing_tasks={"dialog_reply_task": "timeout"})

    result = provider.generate(_request())

    assert result.status == "error"
    assert result.error is not None
    assert result.error.type == "timeout"
    assert result.error.retriable is True


def test_fake_provider_keeps_legacy_reply_task_alias() -> None:
    provider = FakeProvider(task_outputs={"dialog_reply_task": {"text": "legacy", "json": {"answer": "yes"}}})

    result = provider.generate(_request(task="dialog_reply_task"))

    assert result.status == "ok"
    assert result.text == "legacy"
