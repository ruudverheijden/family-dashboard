"""Opt-in checks against the built runtime, without real configuration or data."""

import os
import subprocess

import pytest


@pytest.mark.skipif(
    not os.getenv("CONTAINER_TEST_IMAGE"), reason="requires a built image and local Docker daemon"
)
def test_container_security_and_runtime():
    script = """
import os
import sqlite3
import subprocess
import tempfile
import zlib
from datetime import datetime, timedelta
from importlib.metadata import version as package_version
from importlib.util import find_spec
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from app.application import create_app
from app.config import AppConfig

assert os.getuid() == os.getgid() == 10001
assert tuple(map(int, package_version('python-dotenv').split('.'))) >= (1, 2, 2)
assert find_spec('pip') is None
assert list(Path('/lib').glob('ld-musl-*.so.1'))
assert not list(Path('/lib').glob('ld-linux*'))
packages = subprocess.check_output(['apk', '--no-network', 'info'], text=True).splitlines()
assert not {'glibc', 'gcompat', 'libc6-compat'} & set(packages)
version = subprocess.check_output(
    ['apk', '--no-network', 'list', '--installed', 'zlib'], text=True
).split()[0]
assert version.startswith('zlib-'), version
comparison = subprocess.check_output(
    ['apk', '--no-network', 'version', '-t', version.removeprefix('zlib-'), '1.3.2-r1'],
    text=True
).strip()
assert comparison in ('=', '>'), version
assert tuple(map(int, zlib.ZLIB_RUNTIME_VERSION.split('.'))) >= (1, 3, 2)
assert zlib.decompress(zlib.compress(b'container regression')) == b'container regression'
zone = ZoneInfo('Europe/Amsterdam')
assert datetime(2026, 1, 1, tzinfo=zone).utcoffset() == timedelta(hours=1)
assert datetime(2026, 7, 1, tzinfo=zone).utcoffset() == timedelta(hours=2)
for directory in ('/data', '/cache'):
    assert os.access(directory, os.W_OK)
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    config = AppConfig(root / 'data', root / 'cache', 'fictitious-password',
                       background_enabled=False)
    with TestClient(create_app(config)) as client:
        assert client.get('/api/health').status_code == 200
        assert client.get('/').status_code == 200
        assert client.get('/api/state').status_code == 200
    with sqlite3.connect(root / 'data' / 'family.db') as connection:
        assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
print(version, zlib.ZLIB_RUNTIME_VERSION, 'musl; runtime checks passed')
"""
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--tmpfs=/tmp:size=32m",
            "--tmpfs=/data:uid=10001,gid=10001",
            "--tmpfs=/cache:uid=10001,gid=10001",
            "--entrypoint=python",
            os.environ["CONTAINER_TEST_IMAGE"],
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
