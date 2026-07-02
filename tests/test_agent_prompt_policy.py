from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


IMAGE_AGENT_PACKAGES = (
    "human_identity_agent",
    "garment_identity_agent",
    "material_texture_agent",
    "try_on_agent",
    "quality_verifier_agent",
    "repair_agent",
    "fashion_stylist_agent",
)

CONTRACT_VERSION_BY_AGENT = {
    "human_identity_agent": "human_identity.contract.v2",
    "garment_identity_agent": "garment_identity.contract.v2",
    "material_texture_agent": "material_texture.contract.v2",
    "try_on_agent": "try_on.contract.v2",
    "quality_verifier_agent": "quality_verifier.contract.v2",
    "repair_agent": "repair.contract.v2",
}

REQUIRED_PROMPT_SECTIONS = (
    "Role:",
    "Authoritative inputs:",
    "Required analysis:",
    "Allowed decisions:",
    "Forbidden actions:",
    "Output contract:",
    "Confidence policy:",
    "Evidence policy:",
    "Uncertainty policy:",
    "Safety policy:",
)


@pytest.mark.parametrize("package_name", IMAGE_AGENT_PACKAGES)
def test_image_agent_prompts_are_versioned_and_follow_enterprise_policy(package_name: str) -> None:
    prompt_module = import_module(f"src.adk_agents.{package_name}.prompt_config")
    instruction_name = next(name for name in vars(prompt_module) if name.endswith("_INSTRUCTION"))
    instruction = getattr(prompt_module, instruction_name)

    assert prompt_module.AGENT_NAME == package_name
    assert prompt_module.PROMPT_VERSION == f"{package_name.removesuffix('_agent')}.v1"
    assert prompt_module.CONTRACT_VERSION == CONTRACT_VERSION_BY_AGENT.get(
        package_name,
        f"{package_name.removesuffix('_agent')}.contract.v1",
    )
    for section in REQUIRED_PROMPT_SECTIONS:
        assert section in instruction


@pytest.mark.parametrize("package_name", IMAGE_AGENT_PACKAGES)
def test_image_agent_deploy_configs_bind_versions_and_semantic_failure_policy(package_name: str) -> None:
    deploy_module = import_module(f"src.adk_agents.{package_name}.deploy_config")
    config_class = next(
        value
        for name, value in vars(deploy_module).items()
        if name.endswith("DeployConfig") and isinstance(value, type)
    )
    config = config_class()

    assert config.prompt_version.endswith(".v1")
    assert config.contract_version == CONTRACT_VERSION_BY_AGENT.get(
        package_name,
        f"{package_name.removesuffix('_agent')}.contract.v1",
    )
    assert config.output_repair_policy == "transport_only"
    assert config.semantic_failure_policy == "reject"


def test_image_agent_packages_do_not_use_any() -> None:
    violations: list[str] = []
    for package_name in IMAGE_AGENT_PACKAGES:
        for path in Path(f"src/adk_agents/{package_name}").glob("*.py"):
            if "Any" in path.read_text(encoding="utf-8"):
                violations.append(str(path))

    assert violations == []


def test_try_on_instruction_prompt_requires_generation_exclusions() -> None:
    prompt_module = import_module("src.adk_agents.try_on_agent.prompt_config")
    instruction = prompt_module.TRY_ON_INSTRUCTION

    assert "generation_exclusions must be non-empty" in instruction
    assert "do not alter face or identity" in instruction
    assert "do not reshape body or proportions" in instruction
    assert "do not change pose" in instruction


def test_quality_verifier_prompt_rejects_blocking_identity_garment_and_anatomy_defects() -> None:
    prompt_module = import_module("src.adk_agents.quality_verifier_agent.prompt_config")
    instruction = prompt_module.QUALITY_VERIFIER_INSTRUCTION

    assert "Missing key garment details are blocking defects" in instruction
    assert "Severe hand, finger, neck, waist, or limb anatomy defects are blocking defects" in instruction
    assert "Blocking defects must return reject" in instruction


def test_garment_identity_prompt_prioritizes_outerwear_for_shirt_jackets() -> None:
    prompt_module = import_module("src.adk_agents.garment_identity_agent.prompt_config")
    instruction = prompt_module.GARMENT_IDENTITY_INSTRUCTION

    assert "shirt jacket" in instruction
    assert "shacket" in instruction
    assert "quilted jacket" in instruction
    assert "outerwear" in instruction
