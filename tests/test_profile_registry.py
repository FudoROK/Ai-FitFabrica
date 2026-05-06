from __future__ import annotations

import pytest

from src.llm.profiles import MemoryProfile, ProfileRegistry, ReplyProfile


def test_profile_registry_resolves_reply_profile():
    registry = ProfileRegistry()

    profile = registry.get_profile(flow="primary_agent_reply_task")

    assert isinstance(profile, ReplyProfile)


def test_profile_registry_resolves_memory_profile():
    registry = ProfileRegistry()

    profile = registry.get_profile(flow="memory")

    assert isinstance(profile, MemoryProfile)


def test_profile_registry_rejects_unknown_flow():
    registry = ProfileRegistry()

    with pytest.raises(ValueError, match="unknown_profile_flow"):
        registry.get_profile(flow="unknown")
