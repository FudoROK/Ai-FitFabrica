"""Guardrails for pre-billing runtime and frontend environment examples."""

from pathlib import Path


BACKEND_ENV_EXAMPLES = (
    Path(".env.example"),
    Path(".env.portable-staging.example"),
    Path(".env.portable-remote-staging.example"),
)

BACKEND_REQUIRED_KEYS = (
    "STATUS_ENDPOINT_TOKEN",
    "ADMIN_API_TOKEN",
    "ALLOW_UNSAFE_ADMIN_HEADER_AUTH",
    "AUTH_PROVIDER",
    "AUTH_SESSION_COOKIE_NAME",
    "ENABLE_ADMIN_TAXONOMY",
    "ENABLE_ADMIN_BUSINESS_CATALOG",
    "ENABLE_ADMIN_COSTS",
    "BILLING_CORE_ENABLED",
    "ENABLE_SEARCH_ENGINE_DISCOVERY",
    "SEARCH_ENGINE_DISCOVERY_PROVIDER",
    "SEARCH_ENGINE_DISCOVERY_DAILY_LIMIT",
    "SEARCH_ENGINE_DISCOVERY_API_KEY",
    "LLM_PROVIDER",
    "LLM_GATEWAY_MODE",
    "POSTGRES_DSN",
    "REDIS_URL",
    "OBJECT_STORAGE_BACKEND",
    "QDRANT_URL",
    "OPERATIONS_QUEUE_BACKEND",
    "TRY_ON_GENERATION_BACKEND",
    "ENABLE_REAL_TRY_ON_GENERATION",
)

FRONTEND_REQUIRED_KEYS = (
    "NEXT_PUBLIC_API_BASE_URL",
    "NEXT_PUBLIC_ENABLE_ADMIN_READINESS_UI",
    "NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_CATALOG_UI",
    "NEXT_PUBLIC_ENABLE_ADMIN_TAXONOMY_UI",
    "NEXT_PUBLIC_ENABLE_ADMIN_BUSINESS_ACCOUNTS_UI",
)


def test_backend_env_examples_cover_pre_billing_runtime_contract() -> None:
    """Backend env examples must expose every operator-controlled pre-billing switch."""
    for path in BACKEND_ENV_EXAMPLES:
        source = path.read_text(encoding="utf-8")
        missing = [key for key in BACKEND_REQUIRED_KEYS if key not in source]

        assert not missing, f"{path} is missing: {', '.join(missing)}"


def test_frontend_firebase_env_example_covers_admin_readiness_contract() -> None:
    """Firebase frontend builds must document all public admin/readiness gates."""
    source = Path("apps/web/.env.firebase.example").read_text(encoding="utf-8")
    missing = [key for key in FRONTEND_REQUIRED_KEYS if key not in source]

    assert not missing, f"apps/web/.env.firebase.example is missing: {', '.join(missing)}"


def test_deploy_runbook_mentions_public_frontend_admin_flags() -> None:
    """Deploy docs must show which internal frontend flags are compiled into staging."""
    source = Path("docs/runbooks/deploy_backend_and_frontend_ru.md").read_text(encoding="utf-8")
    missing = [key for key in FRONTEND_REQUIRED_KEYS if key not in source]

    assert not missing, f"deploy runbook is missing: {', '.join(missing)}"
