from src.llm.core.request import LLMRequest
from src.llm.core.result import LLMResult
from src.llm.core.types import LLMError, Usage


def test_core_models_can_be_constructed():
    request = LLMRequest(
        task="primary_agent_reply_task",
        input="hello",
        structured_output={"schema": {"type": "object"}},
        metadata={"trace_id": "abc"},
        timeout_s=10,
        max_retries=2,
        temperature=0.1,
    )

    error = LLMError(type="timeout", message_redacted="timed out", retriable=True, http_status=504)
    usage = Usage(input_tokens=10, output_tokens=12, total_tokens=22)
    result = LLMResult(status="error", provider="fake", model="fake-model", usage=usage, error=error)

    assert request.input == "hello"
    assert result.error is not None
    assert result.error.type == "timeout"
    assert result.usage is not None
    assert result.usage.total_tokens == 22
