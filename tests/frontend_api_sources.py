from pathlib import Path


def api_client_source() -> str:
    api_dir = Path("apps/web/src/lib/api")
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(api_dir.glob("**/*.ts")))
