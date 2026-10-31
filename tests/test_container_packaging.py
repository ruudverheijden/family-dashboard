"""Opt-in regression using Docker's actual build-context filtering."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_CONTAINER_TESTS") != "1", reason="requires opt-in and a local Docker daemon"
)
def test_docker_context_excludes_local_data_and_nested_bytecode(tmp_path):
    context = tmp_path / "context"
    context.mkdir()
    root = Path(__file__).resolve().parents[1]
    shutil.copyfile(root / ".dockerignore", context / ".dockerignore")
    excluded = [
        ".env",
        ".env.production",
        ".env.local",
        ".git/config",
        "data/family.db",
        "cache/photo.jpg",
        "backups/family.db",
        "test-results/trace.zip",
        "node_modules/package/index.js",
        "app/__pycache__/config.cpython-314.pyc",
        "app/services/__pycache__/settings.cpython-314.pyc",
        "app/integrations/legacy.pyc",
        "app/integrations/legacy.pyo",
    ]
    for name in [*excluded, ".env.example", "app/main.py", "app/static/app.js"]:
        target = context / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fictitious packaging fixture\n")
    output = tmp_path / "output"
    subprocess.run(
        [
            "docker",
            "build",
            "--network=none",
            "--file",
            "-",
            "--output",
            f"type=local,dest={output}",
            str(context),
        ],
        input="FROM scratch\nCOPY . /\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=120,
    )
    assert (output / "app/main.py").is_file()
    assert (output / "app/static/app.js").is_file()
    assert (output / ".env.example").is_file()
    assert all(not (output / name).exists() for name in excluded)
