from src.adk_agents.quality_verifier_agent.prompt_config import QUALITY_VERIFIER_INSTRUCTION
from src.adk_agents.try_on_agent.prompt_config import TRY_ON_INSTRUCTION


def test_try_on_instruction_prompt_requires_selected_wear_control_compliance() -> None:
    prompt = TRY_ON_INSTRUCTION.lower()

    assert "wear_control_selections" in prompt
    assert "do not contradict" in prompt
    assert "selected wear control" in prompt


def test_quality_verifier_prompt_requires_wear_control_match_check() -> None:
    prompt = QUALITY_VERIFIER_INSTRUCTION.lower()

    assert "wear_control_match" in prompt
    assert "selected wear control" in prompt
    assert "do not return pass" in prompt


def test_quality_verifier_prompt_calibrates_neckline_and_color_mismatch() -> None:
    prompt = QUALITY_VERIFIER_INSTRUCTION.lower()

    assert "normal collar opening" in prompt
    assert "unapproved extra garment" in prompt
    assert "color mismatches must not pass" in prompt
    assert "minor local color defects" in prompt
