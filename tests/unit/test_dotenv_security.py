"""Guard the dependency fix for CVE-2026-28684 with fictitious files only."""

import errno
import os

import pytest
from dotenv import set_key, unset_key


@pytest.mark.parametrize("operation", ["set", "unset"])
def test_dotenv_rewrite_does_not_overwrite_symlink_target(tmp_path, monkeypatch, operation):
    target = tmp_path / "unrelated.conf"
    original = "FICTITIOUS_KEY=keep-this-value\n"
    target.write_text(original)
    env_file = tmp_path / ".env"
    env_file.symlink_to(target)

    def cross_device_rename(*args, **kwargs):
        raise OSError(errno.EXDEV, "Simulated cross-device rename")

    # The vulnerable dependency falls back to copying over the symlink target.
    monkeypatch.setattr(os, "rename", cross_device_rename)
    if operation == "set":
        result = set_key(env_file, "FICTITIOUS_KEY", "replacement")
    else:
        result = unset_key(env_file, "FICTITIOUS_KEY")

    assert result[0] is True
    assert target.read_text() == original
    assert not env_file.is_symlink()
