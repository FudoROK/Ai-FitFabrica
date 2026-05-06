from src.llm.provider_routing import select_provider_path


def test_memory_daily_sync_routes_to_memory_daily_runtime_path() -> None:
    decision = select_provider_path("memory_daily_sync_task")

    assert decision.path_name == "memory_daily_runtime"
    assert decision.structured_provider_used is False


def test_existing_tasks_keep_legacy_paths() -> None:
    assert select_provider_path("primary_agent_reply_task").path_name == "agent_runtime"
