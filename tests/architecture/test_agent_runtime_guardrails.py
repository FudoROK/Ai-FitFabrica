from __future__ import annotations

import ast
from pathlib import Path


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports


def test_routes_and_use_cases_do_not_import_adk_agent_roots_directly() -> None:
    violations: list[str] = []
    for root in (Path("src/entrypoints"), Path("src/use_cases")):
        for path in root.rglob("*.py"):
            if path.parent == Path("src/entrypoints") and path.name.startswith("runtime_dependency_"):
                continue
            for imported in _imports(path):
                if imported == "src.adk_agents" or imported.startswith("src.adk_agents."):
                    violations.append(f"{path}:{imported}")

    assert violations == []


def test_product_agents_do_not_import_agent_gateway_or_other_agent_packages() -> None:
    violations: list[str] = []
    for path in Path("src/adk_agents").rglob("*.py"):
        for imported in _imports(path):
            if imported.startswith("src.use_cases.agents") or imported.startswith("src.adapters.agents"):
                violations.append(f"{path}:{imported}")

    assert violations == []


def test_business_layers_do_not_import_provider_sdks() -> None:
    """Keep provider replacement isolated from domain and workflow code."""
    forbidden_prefixes = (
        "anthropic",
        "google.adk",
        "google.cloud.aiplatform",
        "google.generativeai",
        "ollama",
        "openai",
        "vertexai",
    )
    violations: list[str] = []
    for root in (Path("src/domain"), Path("src/use_cases"), Path("src/entrypoints")):
        for path in root.rglob("*.py"):
            for imported in _imports(path):
                if imported.startswith(forbidden_prefixes):
                    violations.append(f"{path}:{imported}")

    assert violations == []


def test_provider_contour_does_not_use_deprecated_vertex_generative_modules() -> None:
    """Keep Gemini generation on Google Gen AI SDK before Vertex SDK removal."""
    forbidden = (
        "vertexai.generative_models",
        "vertexai.language_models",
        "vertexai.vision_models",
        "vertexai.tuning",
        "vertexai.caching",
    )
    violations: list[str] = []
    for path in Path("src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for module_name in forbidden:
            if module_name in text:
                violations.append(f"{path}:{module_name}")

    assert violations == []
