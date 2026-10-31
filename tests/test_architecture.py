"""Application isolation, atomic writes and integration publication boundaries."""

import asyncio
import hashlib
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app import config, scheduler
from app.application import create_app
from app.config import AppConfig
from app.errors import DomainError
from app.integrations import caldav, immich
from app.services import entities

HEADERS = {"X-Family-Request": "1"}


@pytest.fixture
def client(tmp_path):
    configuration = AppConfig(
        tmp_path / "data", tmp_path / "cache", "test-password", background_enabled=False
    )
    with TestClient(create_app(configuration), headers=HEADERS) as client:
        assert client.post("/api/login", json={"password": "test-password"}).status_code == 200
        yield client


def configure(client, **changes):
    body = client.get("/api/admin/settings").json()
    body.update(changes)
    response = client.post("/api/admin/settings", json=body)
    assert response.status_code == 200, response.text


def photo_response(**kwargs):
    return httpx.Response(
        200, request=httpx.Request("GET", "https://photos.example.test"), **kwargs
    )


def test_explicit_applications_isolate_data_sessions_and_photos(tmp_path, monkeypatch):
    def unexpected(*args):
        pytest.fail("An explicitly configured application must not read .env")

    monkeypatch.setattr(config, "load_environment", unexpected)
    configs = [
        AppConfig(tmp_path / name, tmp_path / (name + "-cache"), name, background_enabled=False)
        for name in ("first", "second")
    ]
    with TestClient(create_app(configs[0]), headers=HEADERS) as first:
        with TestClient(create_app(configs[1]), headers=HEADERS) as second:
            assert first.post("/api/login", json={"password": "first"}).status_code == 200
            assert second.post("/api/login", json={"password": "first"}).status_code == 401
            second.cookies.set("family_admin", first.cookies.get("family_admin"))
            assert second.get("/api/admin/settings").status_code == 401
            response = first.post(
                "/api/entities/groceries",
                json={
                    "id": str(uuid.uuid4()),
                    "request_id": str(uuid.uuid4()),
                    "version": 0,
                    "body": {"name": "Only in first"},
                },
            )
            assert response.status_code == 200
            first.app.state.runtime.photos.assets = {"one": {"id": "one"}}
            assert first.get("/api/state").json()["groceries"]
            assert second.get("/api/state").json()["groceries"] == []
            assert second.get("/api/state").json()["photos"] == []


@pytest.mark.parametrize("failure", [False, True])
def test_slow_caldav_does_not_block_photos_or_settings_and_discards_old_results(
    client, monkeypatch, failure
):
    rt = client.app.state.runtime
    account = {
        "id": str(uuid.uuid4()),
        "url": "https://calendar.example.test",
        "username": "test",
        "password": "private",
        "calendars": [
            {"url": "https://calendar.example.test/family", "name": "Family", "member": ""}
        ],
    }
    configure(client, caldav=[account])
    asset = str(uuid.uuid4())
    rt.photos.assets = {asset: {"id": asset}}
    rt.photos.cache.mkdir(parents=True, exist_ok=True)
    (rt.photos.cache / hashlib.sha256(asset.encode()).hexdigest()).write_bytes(b"cached-photo")
    started, release = threading.Event(), threading.Event()

    def slow_client(account):
        started.set()
        assert release.wait(5)
        if failure:
            raise OSError("private upstream content")

        class Remote:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def principal(self):
                return self

            url = "https://calendar.example.test/family"

            def calendars(self):
                return [self]

            def search(self, **kwargs):
                return [SimpleNamespace(data="fixture")]

        return Remote()

    monkeypatch.setattr(caldav, "client", slow_client)
    monkeypatch.setattr(
        caldav, "expand_ics", lambda *args: [{"id": "stale", "title": "Removed calendar event"}]
    )
    with ThreadPoolExecutor(max_workers=3) as pool:
        running = pool.submit(rt.calendars.sync)
        try:
            assert started.wait(2)
            assert pool.submit(rt.photos.photo, asset).result(timeout=2) == b"cached-photo"
            pool.submit(configure, client, caldav=[]).result(timeout=2)
            assert pool.submit(client.get, "/api/state").result(timeout=2).status_code == 200
        finally:
            release.set()
        running.result(timeout=2)
    state = client.get("/api/state").json()
    assert state["events"] == []
    assert "caldav:" + account["id"] not in state["status"]


@pytest.mark.parametrize("failure", [False, True])
def test_album_refresh_cannot_publish_after_selection_changes(client, monkeypatch, failure):
    rt = client.app.state.runtime
    album, asset = str(uuid.uuid4()), str(uuid.uuid4())
    configure(
        client, immich_url="https://photos.example.test", immich_key="private", albums=[album]
    )
    started, release = threading.Event(), threading.Event()

    def fetch(*args):
        started.set()
        assert release.wait(5)
        if failure:
            raise OSError("private upstream content")
        return photo_response(
            json={"albumName": "Old selection", "assets": [{"id": asset, "type": "IMAGE"}]}
        )

    monkeypatch.setattr(immich, "immich_get", fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(rt.photos.sync)
        try:
            assert started.wait(2)
            pool.submit(configure, client, albums=[]).result(timeout=2)
        finally:
            release.set()
        running.result(timeout=2)
    assert rt.photos.snapshot() == []
    assert client.get("/api/photos/" + asset).status_code == 404
    with rt.database.connect() as db:
        assert db.execute("SELECT body FROM status WHERE id='immich'").fetchone() is None


def test_in_flight_photo_is_neither_returned_nor_cached_after_revocation(client, monkeypatch):
    rt = client.app.state.runtime
    album, asset = str(uuid.uuid4()), str(uuid.uuid4())
    configure(
        client, immich_url="https://photos.example.test", immich_key="private", albums=[album]
    )
    rt.photos.assets = {asset: {"id": asset}}
    started, release = threading.Event(), threading.Event()

    def fetch(*args):
        started.set()
        assert release.wait(5)
        return photo_response(content=b"private-image", headers={"content-type": "image/jpeg"})

    monkeypatch.setattr(immich, "immich_get", fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(client.get, "/api/photos/" + asset)
        try:
            assert started.wait(2)
            pool.submit(configure, client, albums=[]).result(timeout=2)
        finally:
            release.set()
        response = running.result(timeout=2)
    assert response.status_code == 404
    assert b"private-image" not in response.content
    assert list(rt.photos.cache.iterdir()) == []


def test_unchanged_album_refresh_preserves_in_flight_photo(client, monkeypatch):
    rt = client.app.state.runtime
    album, asset = str(uuid.uuid4()), str(uuid.uuid4())
    configure(
        client, immich_url="https://photos.example.test", immich_key="private", albums=[album]
    )
    rt.photos.assets = {asset: {"id": asset, "album": "Family"}}
    started, release = threading.Event(), threading.Event()

    def fetch(cfg, path):
        if path.startswith("/albums/"):
            return photo_response(
                json={"albumName": "Family", "assets": [{"id": asset, "type": "IMAGE"}]}
            )
        started.set()
        assert release.wait(5)
        return photo_response(content=b"photo", headers={"content-type": "image/jpeg"})

    monkeypatch.setattr(immich, "immich_get", fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(rt.photos.photo, asset)
        try:
            assert started.wait(2)
            pool.submit(rt.photos.sync).result(timeout=2)
        finally:
            release.set()
        assert running.result(timeout=2) == b"photo"


def test_completion_rolls_back_when_point_write_fails(client, monkeypatch):
    def create(kind, body):
        entity_id = str(uuid.uuid4())
        response = client.post(
            "/api/entities/" + kind,
            json={
                "id": entity_id,
                "request_id": str(uuid.uuid4()),
                "version": 0,
                "body": body,
            },
        )
        assert response.status_code == 200, response.text
        return entity_id

    member = create("members", {"name": "Test", "color": "#112233"})
    day = client.get("/api/state").json()["day"]
    create(
        "tasks",
        {
            "title": "Task",
            "date": day,
            "members": [member],
            "repeat": "once",
            "mode": "individual",
            "points": 5,
        },
    )
    before = client.get("/api/state").json()
    run = before["runs"][0]
    history = client.get("/api/history").json()
    request_id = str(uuid.uuid4())

    def fail(*args):
        raise DomainError(503, "Temporary point storage failure")

    monkeypatch.setattr(entities, "update_completion_points", fail)
    response = client.post(
        "/api/entities/runs",
        json={
            "id": run["id"],
            "version": run["version"],
            "request_id": request_id,
            "body": {"done": [0]},
        },
    )
    assert response.status_code == 503
    after = client.get("/api/state").json()
    assert after["runs"] == before["runs"]
    assert after["point_transactions"] == before["point_transactions"]
    assert client.get("/api/history").json() == history
    with client.app.state.runtime.database.connect() as db:
        assert db.execute("SELECT 1 FROM requests WHERE id=?", (request_id,)).fetchone() is None


def test_background_error_is_sanitized_and_other_jobs_continue(caplog):
    async def check():
        progressed = threading.Event()

        def broken():
            raise OSError("secret-password-in-upstream-error")

        tasks = [
            asyncio.create_task(scheduler.repeat(broken, 0.01)),
            asyncio.create_task(scheduler.repeat(progressed.set, 0.01)),
        ]
        try:
            for _ in range(100):
                if progressed.is_set():
                    break
                await asyncio.sleep(0.01)
            assert progressed.is_set()
        finally:
            await scheduler.stop(tasks)

    asyncio.run(check())
    assert "OSError" in caplog.text
    assert "secret-password" not in caplog.text


def test_default_entrypoint_resolves_environment_at_startup_only(tmp_path, monkeypatch):
    configuration = AppConfig(
        tmp_path / "default-data", tmp_path / "default-cache", "test", background_enabled=False
    )
    calls = []

    def from_environment(cls):
        calls.append(True)
        return configuration

    monkeypatch.setattr(AppConfig, "from_environment", classmethod(from_environment))
    from app.main import app

    assert calls == []
    assert not configuration.data_dir.exists()
    with TestClient(app) as client:
        assert calls == [True]
        assert client.get("/api/health").json()["status"] == "ok"
        assert (configuration.data_dir / "family.db").exists()
