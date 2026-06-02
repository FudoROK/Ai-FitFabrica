from __future__ import annotations

from pathlib import Path


def test_fitfabrica_agent_system_plan_exists_and_is_linked_from_master_plan() -> None:
    plan_path = Path("docs/superpowers/plans/2026-06-02-fitfabrica-agent-system-plan.md")
    master_plan = Path("docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md")

    plan_source = plan_path.read_text(encoding="utf-8")
    master_source = master_plan.read_text(encoding="utf-8")

    assert "FitFabrica Agent System Implementation Plan" in plan_source
    assert "src/adk_agents/orchestrator_agent" in plan_source
    assert "src/adk_agents/human_identity_agent" in plan_source
    assert "src/adk_agents/marketplace_agent" in plan_source
    assert "src/runtime_agents/dialog_reply" in plan_source
    assert "2026-06-02-fitfabrica-agent-system-plan.md" in master_source
    assert "- [x] **Step 34: Write a dedicated FitFabrica agent system plan**" in master_source
    assert "src/runtime_agents/dialog_reply" in master_source
