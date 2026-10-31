"""Exercise empty storage, restored ownership and replacement with real containers."""

import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest


@pytest.mark.skipif(
    not os.getenv("CONTAINER_TEST_IMAGE"), reason="requires a built image and local Docker daemon"
)
@pytest.mark.parametrize("storage_kind", ["volume", "bind"])
def test_empty_storage_is_prepared_before_nonroot_app_starts(tmp_path, storage_kind):
    root = Path(__file__).resolve().parents[1]
    image = os.environ["CONTAINER_TEST_IMAGE"]
    project = "storage-regression-" + uuid.uuid4().hex
    volumes = []
    environment = {
        **os.environ,
        "ADMIN_PASSWORD": "fictitious-storage-regression",
        "DASHBOARD_IMAGE": image,
        "DATA_VOLUME": "family-data",
        "CACHE_VOLUME": "family-cache",
        "PORT": "8080",
        "TZ": "Europe/Amsterdam",
        "COOKIE_SECURE": "false",
        "CACHE_MB": "128",
    }

    def docker(*arguments, check=True):
        result = subprocess.run(
            ["docker", *arguments], capture_output=True, text=True, timeout=120, env=environment
        )
        if check:
            assert result.returncode == 0, result.stdout + result.stderr
        return result

    config_path = tmp_path / "compose.json"
    compose = (
        "compose",
        "--project-name",
        project,
        "--env-file",
        str(tmp_path / ".env"),
        "--file",
        str(config_path),
    )
    (tmp_path / ".env").write_text("ADMIN_PASSWORD=fictitious-storage-regression\n")

    try:
        mounts = []
        named_volumes = {}
        for directory in ("data", "cache"):
            name = f"{project}-{directory}"
            docker("volume", "create", name)
            volumes.append(name)
            # nocopy prevents Docker from copying the image's preconfigured ownership.
            docker(
                "run",
                "--rm",
                "--network=none",
                "--user=0:0",
                "--mount",
                f"type=volume,src={name},dst=/storage,volume-nocopy",
                image,
                "python",
                "-c",
                "import os; os.chown('/storage', 0, 0); os.chmod('/storage', 0o755)",
            )
            mount = {"type": storage_kind, "target": f"/{directory}"}
            if storage_kind == "volume":
                key = f"family-{directory}"
                named_volumes[key] = {"external": True, "name": name}
                mount.update(source=key)
            else:
                # A Linux path on the daemon gives real bind-mount permission semantics,
                # independent of Docker Desktop's macOS filesystem sharing behavior.
                location = docker("volume", "inspect", name, "--format", "{{.Mountpoint}}")
                mount.update(source=location.stdout.strip(), bind={"create_host_path": False})
                environment[f"{directory.upper()}_VOLUME"] = location.stdout.strip()
            mounts.append(mount)

        # Resolve the real shared file: exercise both default volume selection and
        # host-path interpolation instead of replacing the service mounts ourselves.
        resolved = docker(
            "compose",
            "--project-name",
            project,
            "--env-file",
            str(tmp_path / ".env"),
            "--file",
            str(root / "compose.yaml"),
            "config",
            "--format",
            "json",
        )
        config = json.loads(resolved.stdout)
        for service in config["services"].values():
            assert service["image"] == image
            for actual, expected in zip(service["volumes"], mounts, strict=True):
                assert actual["type"] == storage_kind
                assert actual["source"] == expected["source"]
                assert actual["target"] == expected["target"]
        config["volumes"] = named_volumes
        dashboard = config["services"]["dashboard"]
        dashboard.pop("ports")
        dashboard.pop("networks", None)
        dashboard["network_mode"] = "none"
        dashboard["healthcheck"] = {"interval": "1s", "start_period": "1s"}
        config_path.write_text(json.dumps(config))

        # Reproduce the original failure before the storage preparer has run.
        first_mount = mounts[0]
        source = volumes[0] if storage_kind == "volume" else first_mount["source"]
        option = ",volume-nocopy" if storage_kind == "volume" else ""
        docker(
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--mount",
            f"type={storage_kind},src={source},dst=/data{option}",
            image,
            "python",
            "-c",
            "import os, sqlite3; assert os.getuid() == 10001; "
            "assert not os.access('/data', os.W_OK); "
            "\ntry: sqlite3.connect('/data/family.db')"
            "\nexcept sqlite3.OperationalError: pass"
            "\nelse: raise AssertionError('Expected inaccessible empty data directory')",
        )

        docker(*compose, "up", "--detach", "--wait", "--wait-timeout", "60")
        container = docker(*compose, "ps", "--quiet", "dashboard").stdout.strip()
        docker(
            "exec",
            container,
            "python",
            "-c",
            "import json, os, sqlite3, urllib.request; "
            "assert os.getuid() == os.getgid() == 10001; "
            "assert urllib.request.urlopen('http://127.0.0.1:8080/').status == 200; "
            "assert urllib.request.urlopen('http://127.0.0.1:8080/api/state').status == 200; "
            "assert os.access('/cache', os.W_OK); "
            "db=sqlite3.connect('/data/family.db'); "
            "assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',); "
            "assert db.execute('SELECT COUNT(*) FROM entities').fetchone() == (0,); "
            "body=json.loads(db.execute('SELECT body FROM settings WHERE id=1').fetchone()[0]); "
            "body['brand_title']='Fictitious preserved settings'; "
            "db.execute('UPDATE settings SET body=? WHERE id=1', (json.dumps(body),)); "
            "db.commit(); db.close()",
        )
        docker(*compose, "down")

        # Simulate copying a consistent backup and cache tree from another machine.
        docker(
            "run",
            "--rm",
            "--network=none",
            "--user=0:0",
            "--mount",
            f"type=volume,src={volumes[0]},dst=/data,volume-nocopy",
            "--mount",
            f"type=volume,src={volumes[1]},dst=/cache,volume-nocopy",
            image,
            "python",
            "-c",
            "import os, sqlite3; from pathlib import Path; "
            "source=sqlite3.connect('/data/family.db'); "
            "target=sqlite3.connect('/data/restored.db'); source.backup(target); "
            "target.close(); source.close(); "
            "os.replace('/data/restored.db', '/data/family.db'); "
            "os.chown('/data/family.db', 12345, 12345); "
            "os.chmod('/data/family.db', 0o666); "
            "\nfor root in ('/data', '/cache'):"
            "\n    nested=Path(root)/'restored'/'nested'; nested.mkdir(parents=True)"
            "\n    marker=nested/'fixture.txt'; marker.write_text('fictitious restored content')"
            "\n    os.symlink('/app/LICENSE', nested/'outside-file')"
            "\n    os.symlink('/app', nested/'outside-directory')"
            "\n    for path in (marker, nested, nested.parent):"
            "\n        os.chown(path, 12345, 12345); os.chmod(path, 0)",
        )
        docker(
            "run",
            "--rm",
            "--network=none",
            "--cap-drop=ALL",
            "--mount",
            f"type=volume,src={volumes[0]},dst=/data,volume-nocopy",
            image,
            "python",
            "-c",
            "from app.db import connect; from pathlib import Path; "
            "\ntry:"
            "\n    with connect(Path('/data')): pass"
            "\nexcept PermissionError: pass"
            "\nelse: raise AssertionError('Expected chmod failure on restored database')",
        )
        docker(*compose, "up", "--detach", "--wait", "--wait-timeout", "60")
        container = docker(*compose, "ps", "--quiet", "dashboard").stdout.strip()
        docker(
            "exec",
            container,
            "python",
            "-c",
            "import json, os, sqlite3, stat; from pathlib import Path; "
            "db=sqlite3.connect('/data/family.db'); "
            "body=json.loads(db.execute('SELECT body FROM settings WHERE id=1').fetchone()[0]); "
            "assert body['brand_title'] == 'Fictitious preserved settings'; "
            "assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',); "
            "db.close(); "
            "assert os.getuid() == 10001; "
            "assert Path('/data/family.db').stat().st_uid == 10001; "
            "assert stat.S_IMODE(Path('/data/family.db').stat().st_mode) == 0o600; "
            "\nfor root in ('/data', '/cache'):"
            "\n    nested=Path(root)/'restored'/'nested'"
            "\n    marker=nested/'fixture.txt'"
            "\n    assert marker.read_text() == 'fictitious restored content'"
            "\n    for path in (Path(root), nested.parent, nested, marker):"
            "\n        info=path.stat(); assert info.st_uid == info.st_gid == 10001"
            "\n        assert stat.S_IMODE(info.st_mode) == (0o700 if path.is_dir() else 0o600)"
            "\n    assert (nested/'outside-file').is_symlink()"
            "\n    assert (nested/'outside-directory').is_symlink()"
            "\nassert Path('/app/LICENSE').stat().st_uid == 0",
        )
        docker(*compose, "down")
        docker(
            "run",
            "--rm",
            "--network=none",
            "--user=0:0",
            "--mount",
            f"type=volume,src={volumes[1]},dst=/cache,volume-nocopy",
            image,
            "python",
            "-c",
            "import os; os.link('/cache/restored/nested/fixture.txt', '/cache/hardlink')",
        )
        rejected = docker(*compose, "run", "--rm", "--no-deps", "storage-init", check=False)
        assert rejected.returncode != 0
        assert "hardlink" in rejected.stdout + rejected.stderr
    except BaseException:
        if config_path.exists():
            print(docker(*compose, "logs", check=False).stdout)
        raise
    finally:
        if config_path.exists():
            docker(*compose, "down", "--volumes", check=False)
        for volume in volumes:
            docker("volume", "rm", volume, check=False)
