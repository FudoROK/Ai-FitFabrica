from __future__ import annotations

import inspect
import pytest

from src.llm.profiles.contracts import FinalProfileInterface, SemanticValidationContext, ValidationResult
from src.llm.profiles.memory_profile import MemoryProfile, MemoryProfileOutput
from src.llm.profiles.reply_profile import ReplyProfile, ReplyProfileOutput
from src.runtime_agents.memory_agent.contracts import DailyMemoryContract


def test_reply_and_memory_profiles_implement_single_canonical_interface():
    reply_profile = ReplyProfile()
    memory_profile = MemoryProfile()

    assert isinstance(reply_profile, FinalProfileInterface)
    assert isinstance(memory_profile, FinalProfileInterface)


def test_reply_and_memory_profile_signatures_are_identical():
    reply_methods = {
        "parse": inspect.signature(ReplyProfile.parse),
        "validate": inspect.signature(ReplyProfile.validate),
        "semantic_validate": inspect.signature(ReplyProfile.semantic_validate),
    }
    memory_methods = {
        "parse": inspect.signature(MemoryProfile.parse),
        "validate": inspect.signature(MemoryProfile.validate),
        "semantic_validate": inspect.signature(MemoryProfile.semantic_validate),
    }

    for method_name in reply_methods:
        assert list(reply_methods[method_name].parameters.keys()) == list(memory_methods[method_name].parameters.keys())


def test_profile_pipeline_stage_results_are_explicit_and_stable():
    reply_profile = ReplyProfile()
    parsed = reply_profile.parse({"reply_text": "ok", "system_payload": {"lead_patch": {}}})

    assert isinstance(parsed, ReplyProfileOutput)
    assert isinstance(reply_profile.validate(parsed), ValidationResult)
    assert isinstance(
        reply_profile.semantic_validate(parsed, SemanticValidationContext(payload={"channel": "telegram"})),
        ValidationResult,
    )

    memory_profile = MemoryProfile()
    typed_payload = DailyMemoryContract.model_validate({"daily_summary": {"summary_text": "x", "open_questions": [], "carry_forward_notes": [], "learned_facts": [], "changed_facts": [], "memory_relevance_flags": []}})
    memory_parsed = memory_profile.parse(typed_payload)

    assert isinstance(memory_parsed, MemoryProfileOutput)
    assert isinstance(memory_profile.validate(memory_parsed), ValidationResult)
    assert isinstance(memory_profile.semantic_validate(memory_parsed, SemanticValidationContext()), ValidationResult)


def test_memory_profile_parse_rejects_non_typed_payload():
    memory_profile = MemoryProfile()
    with pytest.raises(TypeError):
        memory_profile.parse({"memory_payload": {"daily_summary": {"summary_text": "x"}}})
