from __future__ import annotations

import os
import subprocess
import sys


def test_runtime_dependencies_does_not_import_adk_or_vertex_agent_runtime_eagerly() -> None:
    """Importing runtime dependencies alone must not load the heavy ADK/Vertex agent stack."""
    env = os.environ.copy()
    env["ENVIRONMENT"] = "test"
    command = [
        sys.executable,
        "-c",
        (
            "import json, sys; "
            "import src.entrypoints.runtime_dependencies; "
            "print(json.dumps({"
            "'google.adk': 'google.adk' in sys.modules, "
            "'vertexai.preview.reasoning_engines': 'vertexai.preview.reasoning_engines' in sys.modules"
            "}))"
        ),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd="C:\\Code\\Ai Fitfabrica",
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '{"google.adk": false, "vertexai.preview.reasoning_engines": false}'


def test_runtime_dependencies_does_not_import_google_genai_eagerly() -> None:
    """Importing runtime dependencies alone must not load google.genai SDK modules."""
    env = os.environ.copy()
    env["ENVIRONMENT"] = "test"
    command = [
        sys.executable,
        "-c",
        (
            "import json, sys; "
            "import src.entrypoints.runtime_dependencies; "
            "print(json.dumps({"
            "'google.genai': 'google.genai' in sys.modules, "
            "'src.adapters.ai.vertex_virtual_try_on_client': 'src.adapters.ai.vertex_virtual_try_on_client' in sys.modules"
            "}))"
        ),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd="C:\\Code\\Ai Fitfabrica",
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '{"google.genai": false, "src.adapters.ai.vertex_virtual_try_on_client": false}'


def test_runtime_dependencies_does_not_import_firestore_eagerly() -> None:
    """Importing runtime dependencies alone must not load Firestore modules."""
    env = os.environ.copy()
    env["ENVIRONMENT"] = "test"
    command = [
        sys.executable,
        "-c",
        (
            "import json, sys; "
            "import src.entrypoints.runtime_dependencies; "
            "print(json.dumps({"
            "'google.cloud.firestore': 'google.cloud.firestore' in sys.modules, "
            "'src.adapters.database.firestore.firestore_client_factory': 'src.adapters.database.firestore.firestore_client_factory' in sys.modules"
            "}))"
        ),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd="C:\\Code\\Ai Fitfabrica",
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        '{"google.cloud.firestore": false, '
        '"src.adapters.database.firestore.firestore_client_factory": false}'
    )
