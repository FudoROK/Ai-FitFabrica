from src.llm.provider_routing import select_provider_path


def test_existing_tasks_keep_legacy_paths() -> None:
    assert select_provider_path("dialog_reply_task").path_name == "agent_runtime"
