from __future__ import annotations

import inspect

from src.llm.profiles.contracts import FinalProfileInterface, SemanticValidationContext, ValidationResult
from src.llm.profiles.reply_profile import ReplyProfile, ReplyProfileOutput


def test_reply_profile_implements_canonical_interface():
    reply_profile = ReplyProfile()

    assert isinstance(reply_profile, FinalProfileInterface)


def test_reply_profile_interface_shape_is_stable():
    signatures = {
        "parse": inspect.signature(ReplyProfile.parse),
        "validate": inspect.signature(ReplyProfile.validate),
        "semantic_validate": inspect.signature(ReplyProfile.semantic_validate),
    }

    assert list(signatures["parse"].parameters.keys()) == ["self", "raw_payload"]
    assert list(signatures["validate"].parameters.keys()) == ["self", "typed_output"]
    assert list(signatures["semantic_validate"].parameters.keys()) == ["self", "typed_output", "context"]


def test_profile_pipeline_stage_results_are_explicit_and_stable():
    reply_profile = ReplyProfile()
    parsed = reply_profile.parse({"reply_text": "ok", "system_payload": {"lead_patch": {}}})

    assert isinstance(parsed, ReplyProfileOutput)
    assert isinstance(reply_profile.validate(parsed), ValidationResult)
    assert isinstance(
        reply_profile.semantic_validate(parsed, SemanticValidationContext(payload={"channel": "telegram"})),
        ValidationResult,
    )
