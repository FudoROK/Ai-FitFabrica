import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.settings import load_settings

# Minimal defaults for modules that initialize services during import.
os.environ.setdefault("MESSAGING_PROVIDER", "none")
os.environ.setdefault("GCP_PROJECT_ID", "test-project")
os.environ.setdefault("PUBSUB_TOPIC_NAME", "test-topic")
os.environ.setdefault("VERTEX_PROJECT", "test-project")
os.environ.setdefault("VERTEX_LOCATION", "us-central1")
os.environ.setdefault("VERTEX_AGENT_RESOURCE", "test-agent")
os.environ.setdefault("HUBSPOT_PRIVATE_APP_TOKEN", "test-hubspot-token")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MEMORY_SUMMARY_TASK_AUTH_AUDIENCE", "https://tasks.example.test/memory-summary")
os.environ.setdefault(
    "MEMORY_SUMMARY_TASK_ALLOWED_SERVICE_ACCOUNTS",
    "memory-task@test-project.iam.gserviceaccount.com",
)
os.environ.setdefault("DAILY_SUMMARY_CRON_AUTH_AUDIENCE", "https://tasks.example.test/daily-summary")
os.environ.setdefault(
    "DAILY_SUMMARY_CRON_ALLOWED_SERVICE_ACCOUNTS",
    "daily-cron@test-project.iam.gserviceaccount.com",
)


@pytest.fixture(autouse=True)
def _isolate_settings_cache():
    """Ensure cached settings do not leak across tests/process env mutations."""
    load_settings.cache_clear()
    yield
    load_settings.cache_clear()
