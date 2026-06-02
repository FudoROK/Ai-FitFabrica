import logging

from src.utils.log_redaction import (
    RedactingLogFilter,
    install_redaction_logging_policy,
    hash_chat_id,
    redact,
    redact_structure,
)


def test_redact_masks_known_patterns(monkeypatch):
    monkeypatch.setenv("CRM_ACCESS_TOKEN", "crm-token-raw")
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "hs-token-raw")
    text = (
        "https://api.telegram.org/bot123456:ABCdef-token/sendMessage "
        "Authorization: Bearer qwerty crm=crm-token-raw hubspot=hs-token-raw "
        "refresh_token=refresh-123 id_token=eyJabc12345.def67890.ghi11111"
    )
    redacted = redact(text)
    assert "/bot***" in redacted
    assert "Bearer ***" in redacted
    assert "crm-token-raw" not in redacted
    assert "hs-token-raw" not in redacted
    assert "refresh-123" not in redacted
    assert "eyJabc12345.def67890.ghi11111" not in redacted


def test_redact_structure_masks_sensitive_headers_and_pii():
    payload = {
        "headers": {
            "Authorization": "Bearer top-secret",
            "X-Telegram-Bot-Api-Secret-Token": "telegram-secret",
        },
        "contact": {"email": "lead@example.com", "phone": "+15550001", "first_name": "Ada"},
        "provider_error": {"details": "token=abc123", "status": "failed"},
        "items": ["access_token=123", {"client_secret": "xyz"}],
    }

    redacted = redact_structure(payload)
    assert redacted["headers"]["Authorization"] == "***"
    assert redacted["headers"]["X-Telegram-Bot-Api-Secret-Token"] == "***"
    assert redacted["contact"]["email"] == "***"
    assert redacted["contact"]["phone"] == "***"
    assert redacted["contact"]["first_name"] == "***"
    assert redacted["provider_error"]["details"] == "token=***"
    assert redacted["items"][0] == "access_token=***"
    assert redacted["items"][1]["client_secret"] == "***"


def test_redact_structure_preserves_numeric_scalars():
    assert redact_structure(200) == 200
    assert redact_structure(1.5) == 1.5
    assert redact_structure(False) is False


def test_redacting_filter_sanitizes_exception_and_extra(caplog):
    logger = logging.getLogger("tests.redaction.filter")
    logger.setLevel(logging.INFO)
    logger.filters = [RedactingLogFilter()]

    with caplog.at_level(logging.ERROR, logger=logger.name):
        try:
            raise RuntimeError("Authorization: Bearer leak-me")
        except RuntimeError:
            logger.exception(
                "provider_error Authorization: Bearer leak-me",
                extra={
                    "headers": {"Authorization": "Bearer leak-me"},
                    "payload": {"refresh_token": "refresh-leak", "email": "x@y.z"},
                },
            )

    rendered = "\n".join(caplog.messages)
    assert "leak-me" not in rendered
    assert "refresh-leak" not in rendered
    assert "x@y.z" not in rendered
    assert "Bearer ***" in rendered



def test_install_policy_redacts_root_logger(caplog):
    install_redaction_logging_policy()
    root = logging.getLogger()
    with caplog.at_level(logging.ERROR):
        root.error("Authorization: Bearer root-leak")
    assert "root-leak" not in "\n".join(caplog.messages)


def test_install_policy_redacts_child_logger_direct_handler_path():
    install_redaction_logging_policy()
    child = logging.getLogger("tests.redaction.child.handler")
    child.propagate = False
    child.setLevel(logging.INFO)

    captured_messages: list[str] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_messages.append(record.getMessage())

    handler = CaptureHandler()
    child.handlers = [handler]
    child.info("Authorization: Bearer child-leak refresh_token=refresh-leak")

    assert captured_messages
    rendered = "\n".join(captured_messages)
    assert "child-leak" not in rendered
    assert "refresh-leak" not in rendered
    assert "Bearer ***" in rendered


def test_install_policy_is_idempotent_for_root_and_handlers(caplog):
    root = logging.getLogger()
    temp_handler = logging.StreamHandler()
    root.addHandler(temp_handler)
    try:
        install_redaction_logging_policy()
        install_redaction_logging_policy()
        root_filters = [flt for flt in root.filters if isinstance(flt, RedactingLogFilter)]
        handler_filters = [flt for flt in temp_handler.filters if isinstance(flt, RedactingLogFilter)]
        assert len(root_filters) == 1
        assert len(handler_filters) == 1
    finally:
        root.removeHandler(temp_handler)

    install_redaction_logging_policy()
    root = logging.getLogger()
    with caplog.at_level(logging.ERROR):
        root.error("Authorization: Bearer root-leak")
    assert "root-leak" not in "\n".join(caplog.messages)


def test_redacting_filter_preserves_uvicorn_style_numeric_args():
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1", "POST", "/webhook/telegram", "1.1", 200),
        exc_info=None,
    )

    RedactingLogFilter().filter(record)

    assert record.args[-1] == 200
    assert record.getMessage() == '127.0.0.1:1 - "POST /webhook/telegram HTTP/1.1" 200'


def test_hash_chat_id_is_stable():
    assert hash_chat_id("1001") == hash_chat_id(1001)
    assert hash_chat_id("1001") != hash_chat_id("1002")
