from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SCRIPTS_ROOT = REPO_ROOT / "scripts"

FORBIDDEN_LEGACY_PATHS = (
    "src/llm_gateway.py",
    "src/config.py",
    "src/services/context_builder.py",
    "src/services/profile_ingest.py",
    "src/services/hubspot_service.py",
    "src/services/crm/service.py",
    "src/services/crm/idempotency.py",
    "src/integrations/hubspot/hubspot_sync_canon.py",
    "src/olaris",
)

FORBIDDEN_BRIDGE_IMPORTS = (
    "src.services.crm.idempotency",
    "src.integrations.hubspot.hubspot_sync_canon",
)

FORBIDDEN_SCRIPT_PATHS = (
    "scripts/olaris_smoke.py",
)

VENDOR_PREFIXES = (
    "google",
    "vertexai",
    "hubspot",
    "openai",
)

# Protected layers must stay vendor-agnostic.
# Direct vendor SDK imports are allowed only in explicit infra/provider modules.
VENDOR_PROTECTED_ROOTS = (
    "src/domain",
    "src/use_cases",
    "src/llm/core",
    "src/services",
    "src/entrypoints",
)

VENDOR_ALLOWED_PATHS = (
    "src/llm/providers",
    "src/integrations",
    "src/clients",
    "src/entrypoints/policies.py",
    "src/services/pubsub/pubsub_service.py",
    "src/memory_layer/services/memory_summary_service.py",
    "src/services/rate_limit/factory.py", # Rate limiter factory needs to import google.api_core.exceptions
)

IDENTITY_CORE_ROOT = "src/identity_core"
IDENTITY_CORE_FORBIDDEN_IMPORT_SCOPES = (
    "src.firestore",
    "src.services.firestore",
    "src.handlers",
    "src.entrypoints",
    "src.clients.telegram_client",
    "src.use_cases",
    "src.integrations.crm",
    "src.services.crm",
    "src.services.crm.crm_service",
)

IDENTITY_CORE_INTERNAL_SCOPE = "src.services.identity.identity_core_runtime_repositories"
IDENTITY_CORE_INTERNAL_IMPORT_FORBIDDEN_SCOPES = (
    "src/handlers",
    "src/entrypoints",
    "src/adapters/database/firestore",
    "src/services/firestore",
    "src/services/crm",
    "src/integrations/crm",
)

IDENTITY_CORE_CONTRACTS_SCOPE = "src.identity_core.contracts"
IDENTITY_CORE_MODELS_SCOPE = "src.identity_core.models"
IDENTITY_CORE_ALLOWED_RUNTIME_IMPORTERS = (
    "src/identity_core/services/identity_resolution.py",
    "src/identity_core/services/identity_core_runtime_repositories.py",
)

CRM_LAYER_SCOPES = (
    "src/services/crm",
    "src/services/crm/crm_service.py",
    "src/integrations/crm",
)

DIRECT_WRITE_METHODS = {"set", "update", "create", "delete"}

OPENAI_RUNTIME_FORBIDDEN_PATTERNS = (
    'provider="openai"',
    'provider = "openai"',
    "LLM_PROVIDER=openai",
    "OPENAI_API_KEY",
    "openai_vector_store_id",
    "previous_response_id",
    "vector_store_ids",
    "from openai import",
    "import openai",
)

TRANSITIONAL_ALLOWED_FILES = {"src/llm/vertex/vertex_provider.py"}
LEGACY_WRAPPER_NAME_MARKERS = ("legacy", "compat", "bridge", "candidates")

BEHAVIOR_LEAKAGE_FORBIDDEN_PATTERNS = (
    "Ты — цифровой ассистент",
    "Сделай daily_summary",
    "Обнови rolling_summary",
    "Здравствуйте! Я ассистент",
    "Как могу к вам обращаться",
    "extract only what is explicit",
    "if unknown, leave empty",
    "bias toward the most recent language",
)

BEHAVIOR_LEAKAGE_ALLOWED_PATH_PREFIXES = (
    "tests/",
)


@dataclass(frozen=True)
class Violation:
    rule: str
    file: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"rule": self.rule, "file": self.file, "detail": self.detail}


def _iter_python_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.py") if path.is_file())


def _file_to_module(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).with_suffix("")
    return ".".join(rel.parts)


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _resolve_imported_module(module: str | None, node: ast.ImportFrom, file_module: str) -> str:
    if node.level == 0:
        return module or ""

    parts = file_module.split(".")
    keep = max(0, len(parts) - node.level)
    base = parts[:keep]
    if module:
        base.extend(module.split("."))
    return ".".join(base)


def _collect_imports(path: Path) -> list[tuple[str, int]]:
    module = _file_to_module(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            imports.append((_resolve_imported_module(node.module, node, module), node.lineno))
    return imports


def _contains_direct_write_call(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr in DIRECT_WRITE_METHODS):
            continue

        owner_name = ""
        if isinstance(func.value, ast.Name):
            owner_name = func.value.id.lower()
        elif isinstance(func.value, ast.Attribute):
            owner_name = func.value.attr.lower()

        if owner_name and not any(
            token in owner_name for token in ("ref", "doc", "collection", "firestore", "store", "repo")
        ):
            continue
        hits.append(f"line {node.lineno}: .{func.attr}(...) direct write pattern")
    return hits


def _is_single_function_module(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    top_level_functions = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    top_level_classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    return len(top_level_functions) == 1 and len(top_level_classes) == 0


def _has_runtime_consumers(target_path: Path) -> bool:
    target_module = _file_to_module(target_path)
    for path in _iter_python_files(SRC_ROOT):
        if path == target_path:
            continue
        for imported, _line in _collect_imports(path):
            if imported == target_module or imported.startswith(f"{target_module}."):
                return True
    return False


def _path_matches(rel: str, scope: str) -> bool:
    return rel == scope or rel.startswith(f"{scope}/")


def _legacy_path_to_module(path: str) -> str:
    rel = path.removesuffix(".py")
    return rel.replace("/", ".")


def _is_forbidden_import(imported: str, forbidden: tuple[str, ...]) -> bool:
    return any(imported == scope or imported.startswith(f"{scope}.") for scope in forbidden)


def run_architecture_checks() -> list[Violation]:
    violations: list[Violation] = []

    # Import boundaries
    domain_forbidden = (
        "src.services",
        "src.firestore_client",
        "src.integrations",
        "src.llm.providers",
        "src.llm.transport",
        "src.main",
        "src.entrypoints",
        "src.handlers",
        "src.clients",
    )

    for path in _iter_python_files(SRC_ROOT / "domain"):
        for imported, line in _collect_imports(path):
            if _is_forbidden_import(imported, domain_forbidden):
                violations.append(
                    Violation(
                        rule="domain_import_boundary",
                        file=_rel_path(path),
                        detail=f"line {line}: DOMAIN cannot import {imported}",
                    )
                )

    for path in _iter_python_files(SRC_ROOT / "llm" / "core"):
        for imported, line in _collect_imports(path):
            if imported == "src.domain" or imported.startswith("src.domain."):
                violations.append(
                    Violation(
                        rule="llm_core_boundary",
                        file=_rel_path(path),
                        detail=f"line {line}: llm/core cannot import DOMAIN ({imported})",
                    )
                )

    for path in _iter_python_files(SRC_ROOT / "llm" / "providers"):
        for imported, line in _collect_imports(path):
            if imported == "src.domain" or imported.startswith("src.domain."):
                violations.append(
                    Violation(
                        rule="llm_provider_boundary",
                        file=_rel_path(path),
                        detail=f"line {line}: llm/providers cannot import DOMAIN ({imported})",
                    )
                )

    for path in _iter_python_files(SRC_ROOT / "llm" / "transport"):
        for imported, line in _collect_imports(path):
            if imported == "src.domain" or imported.startswith("src.domain."):
                violations.append(
                    Violation(
                        rule="llm_transport_boundary",
                        file=_rel_path(path),
                        detail=f"line {line}: llm/transport cannot import DOMAIN ({imported})",
                    )
                )

    for path in _iter_python_files(SRC_ROOT / "use_cases"):
        for imported, line in _collect_imports(path):
            if imported == "src.integrations.adapters" or imported.startswith("src.integrations.adapters."):
                violations.append(
                    Violation(
                        rule="use_case_concrete_adapter_import",
                        file=_rel_path(path),
                        detail=f"line {line}: use_cases should not import concrete adapters ({imported})",
                    )
                )
            if imported == "src.firestore_client" or imported.startswith("src.firestore_client."):
                violations.append(
                    Violation(
                        rule="use_case_firestore_low_level_import",
                        file=_rel_path(path),
                        detail=f"line {line}: use_cases should not import low-level firestore client",
                    )
                )
            if imported.split(".")[0] in VENDOR_PREFIXES:
                violations.append(
                    Violation(
                        rule="use_case_vendor_import",
                        file=_rel_path(path),
                        detail=f"line {line}: use_cases must not import vendor SDK directly ({imported})",
                    )
                )

    # Identity core layer boundaries
    for path in _iter_python_files(SRC_ROOT / "identity_core"):
        rel = _rel_path(path)
        for imported, line in _collect_imports(path):
            if _is_forbidden_import(imported, IDENTITY_CORE_FORBIDDEN_IMPORT_SCOPES):
                violations.append(
                    Violation(
                        rule="identity_core_runtime_import_boundary",
                        file=rel,
                        detail=f"line {line}: identity_core cannot import runtime/transport/firestore/crm internals ({imported})",
                    )
                )

    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        if rel.startswith(f"{IDENTITY_CORE_ROOT}/"):
            continue
        if not any(_path_matches(rel, scope) for scope in IDENTITY_CORE_INTERNAL_IMPORT_FORBIDDEN_SCOPES):
            continue
        for imported, line in _collect_imports(path):
            if imported == IDENTITY_CORE_INTERNAL_SCOPE or imported.startswith(f"{IDENTITY_CORE_INTERNAL_SCOPE}."):
                violations.append(
                    Violation(
                        rule="identity_core_internal_leakage",
                        file=rel,
                        detail=f"line {line}: runtime/firestore/crm/transport layers cannot import identity resolution runtime internals ({imported})",
                    )
                )

    # Identity authority boundary
    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        if rel.startswith(f"{IDENTITY_CORE_ROOT}/"):
            continue
        if rel in IDENTITY_CORE_ALLOWED_RUNTIME_IMPORTERS:
            continue
        for imported, line in _collect_imports(path):
            if imported == IDENTITY_CORE_CONTRACTS_SCOPE or imported.startswith(f"{IDENTITY_CORE_CONTRACTS_SCOPE}."):
                violations.append(
                    Violation(
                        rule="identity_contract_boundary_leakage",
                        file=rel,
                        detail=f"line {line}: identity contracts are allowed only in runtime identity-resolution boundary services ({imported})",
                    )
                )
            if imported == IDENTITY_CORE_MODELS_SCOPE or imported.startswith(f"{IDENTITY_CORE_MODELS_SCOPE}."):
                violations.append(
                    Violation(
                        rule="identity_model_boundary_leakage",
                        file=rel,
                        detail=f"line {line}: identity models are allowed only in runtime identity-resolution boundary services ({imported})",
                    )
                )

    # CRM is downstream projection and must not depend on identity internals
    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        if not any(_path_matches(rel, scope) for scope in CRM_LAYER_SCOPES):
            continue
        for imported, line in _collect_imports(path):
            if imported.startswith(IDENTITY_CORE_CONTRACTS_SCOPE) or imported.startswith(IDENTITY_CORE_MODELS_SCOPE):
                violations.append(
                    Violation(
                        rule="crm_identity_authority_coupling",
                        file=rel,
                        detail=f"line {line}: CRM projection layer cannot import identity authority internals ({imported})",
                    )
                )

    # Direct firestore writes discipline
    direct_write_allowlist = {
        "src/services/persistence/firestore_repositories.py",
        "src/services/persistence/firestore_lead_persistence.py",
        "src/adapters/database/firestore/storage_primitives.py",
        "src/adapters/database/firestore/lead_store.py",
        "src/adapters/database/firestore/message_store.py",
        "src/adapters/database/firestore/summary_store.py",
        "src/adapters/database/firestore/crm_binding_store.py",
    }
    for path in [*_iter_python_files(SRC_ROOT / "use_cases"), *_iter_python_files(SRC_ROOT / "services")]:
        rel = _rel_path(path)
        if rel in direct_write_allowlist:
            continue
        for hit in _contains_direct_write_call(path):
            violations.append(
                Violation(
                    rule="firestore_write_discipline",
                    file=rel,
                    detail=f"{hit}; direct Firestore writes are forbidden here",
                )
            )

    # Vendor imports inside protected layers
    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        if not any(_path_matches(rel, root) for root in VENDOR_PROTECTED_ROOTS):
            continue
        if any(_path_matches(rel, allowed) for allowed in VENDOR_ALLOWED_PATHS):
            continue
        for imported, line in _collect_imports(path):
            if imported.split(".")[0] in VENDOR_PREFIXES:
                violations.append(
                    Violation(
                        rule="vendor_sdk_boundary",
                        file=rel,
                        detail=(
                            f"line {line}: vendor SDK import in protected layer ({imported}); "
                            "allowed only in approved infra/provider modules"
                        ),
                    )
                )

    # Transitional scope and legacy resurrection
    for legacy in FORBIDDEN_LEGACY_PATHS:
        if (REPO_ROOT / legacy).exists():
            violations.append(
                Violation(
                    rule="legacy_resurrection",
                    file=legacy,
                    detail="legacy/compatibility module must not be present",
                )
            )

    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        for imported, line in _collect_imports(path):
            if _is_forbidden_import(imported, FORBIDDEN_BRIDGE_IMPORTS):
                violations.append(
                    Violation(
                        rule="forbidden_bridge_import",
                        file=rel,
                        detail=f"line {line}: forbidden transitional bridge import ({imported})",
                    )
                )

    forbidden_script_import_modules = tuple(
        _legacy_path_to_module(path) for path in FORBIDDEN_LEGACY_PATHS if path.endswith(".py")
    ) + FORBIDDEN_BRIDGE_IMPORTS

    for path in _iter_python_files(SCRIPTS_ROOT):
        rel = _rel_path(path)
        for imported, line in _collect_imports(path):
            if _is_forbidden_import(imported, forbidden_script_import_modules):
                violations.append(
                    Violation(
                        rule="scripts_forbidden_import",
                        file=rel,
                        detail=f"line {line}: scripts/ cannot import forbidden legacy/transitional path ({imported})",
                    )
                )

    for forbidden_script in FORBIDDEN_SCRIPT_PATHS:
        if (REPO_ROOT / forbidden_script).exists():
            violations.append(
                Violation(
                    rule="scripts_legacy_smoke_resurrection",
                    file=forbidden_script,
                    detail="legacy smoke script must not be present",
                )
            )

    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        lower_name = path.name.lower()
        if any(marker in lower_name for marker in ("legacy", "compat", "bridge")):
            if rel not in TRANSITIONAL_ALLOWED_FILES:
                violations.append(
                    Violation(
                        rule="transitional_scope_expansion",
                        file=rel,
                        detail="new transitional-looking module detected (legacy/compat/bridge in filename)",
                    )
                )

    for path in _iter_python_files(SRC_ROOT / "llm" / "providers"):
        rel = _rel_path(path)
        lower_name = path.name.lower()
        if not any(marker in lower_name for marker in LEGACY_WRAPPER_NAME_MARKERS):
            continue
        if not _is_single_function_module(path):
            continue
        if _has_runtime_consumers(path):
            continue
        violations.append(
            Violation(
                rule="orphan_legacy_wrapper",
                file=rel,
                detail=(
                    "single-function legacy/compat wrapper module has no runtime consumers; "
                    "remove it or wire explicit runtime usage"
                ),
            )
        )

    vertex_path = REPO_ROOT / "src/llm/vertex/vertex_provider.py"
    if not vertex_path.exists():
        violations.append(
            Violation(
                rule="transitional_scope_missing_vertex",
                file="src/llm/vertex/vertex_provider.py",
                detail="expected explicit transitional vertex_provider scaffold is missing",
            )
        )

    adapters_dir = REPO_ROOT / "src/adapters"
    if not adapters_dir.exists():
        violations.append(
            Violation(
                rule="transitional_scope_missing_adapters",
                file="src/adapters",
                detail="expected explicit transitional adapters directory is missing",
            )
        )

    # OpenAI anti-regression guard: code/build/config only
    runtime_targets = list(SRC_ROOT.rglob("*.py"))

    runtime_targets.extend(
        [
            REPO_ROOT / ".env.example",
            REPO_ROOT / "requirements.txt",
            REPO_ROOT / "requirements-dev.txt",
        ]
    )
    for path in runtime_targets:
        if not path.exists() or not path.is_file():
            continue
        rel = _rel_path(path)
        body = path.read_text(encoding="utf-8")
        for pattern in OPENAI_RUNTIME_FORBIDDEN_PATTERNS:
            if pattern in body:
                violations.append(
                    Violation(
                        rule="openai_runtime_regression",
                        file=rel,
                        detail=f"forbidden OpenAI runtime snippet detected: {pattern}",
                    )
                )

    # Backend behavior text leakage: code only, tests excluded
    for path in _iter_python_files(SRC_ROOT):
        rel = _rel_path(path)
        if rel.startswith(BEHAVIOR_LEAKAGE_ALLOWED_PATH_PREFIXES):
            continue
        body = path.read_text(encoding="utf-8")
        for pattern in BEHAVIOR_LEAKAGE_FORBIDDEN_PATTERNS:
            if pattern in body:
                violations.append(
                    Violation(
                        rule="backend_behavior_text_leakage",
                        file=rel,
                        detail=f"forbidden behavior/instruction text detected: {pattern!r}",
                    )
                )

    return violations


def format_report(violations: list[Violation]) -> str:
    if not violations:
        return "ARCHITECTURE CHECK PASSED: no violations found."
    lines = ["ARCHITECTURE CHECK FAILED:"]
    for idx, violation in enumerate(violations, 1):
        lines.append(f"{idx}. [{violation.rule}] {violation.file} -> {violation.detail}")
    return "\n".join(lines)


def to_json(violations: list[Violation]) -> str:
    return json.dumps({"violations": [v.as_dict() for v in violations]}, ensure_ascii=False, indent=2)