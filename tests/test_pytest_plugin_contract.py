from __future__ import annotations

import configparser
from pathlib import Path


def _read_required_plugins(pytest_ini_path: Path) -> list[str]:
    parser = configparser.ConfigParser()
    parser.read(pytest_ini_path, encoding="utf-8")
    raw_value = parser.get("pytest", "required_plugins", fallback="")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _read_dev_requirements(requirements_dev_path: Path) -> str:
    return requirements_dev_path.read_text(encoding="utf-8")


def test_required_pytest_plugins_are_declared_in_dev_dependencies() -> None:
    required_plugins = _read_required_plugins(Path("pytest.ini"))
    requirements_dev = _read_dev_requirements(Path("requirements-dev.txt"))

    assert "pytest-asyncio" in required_plugins
    for plugin in required_plugins:
        assert plugin in requirements_dev, f"{plugin} is required by pytest.ini but not declared in requirements-dev.txt"
