import asyncio
import base64
import hashlib
import json
import os
import re
import sqlite3
import stat
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException, Request, Response
from fastapi.testclient import TestClient

from app import auth, backup, db, security
from app.application import create_app
from app.config import AppConfig, load_environment
from app.integrations import caldav, immich
from app.schemas import Login

HEAD = {"X-Family-Request": "1"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Legacy DB assertions use this helper path; the app receives explicit configuration.
    monkeypatch.setattr(db, "DATA", tmp_path / "data")
    config = AppConfig(
        tmp_path / "data", tmp_path / "cache", "fictional-test-password", background_enabled=False
    )
    with TestClient(create_app(config), headers=HEAD) as c:
        c.app.state.runtime.auth.sessions["test-admin"] = 10**12
        c.cookies.set("family_admin", "test-admin")
        yield c


def create(c, kind, body, id=None, version=0, request_id=None, action="save"):
    id = id or str(uuid.uuid4())
    result = c.post(
        "/api/entities/" + kind,
        json={
            "request_id": request_id or str(uuid.uuid4()),
            "id": id,
            "version": version,
            "body": body,
            "action": action,
        },
    )
    return id, result


def test_health_reports_release_version(client):
    assert client.get("/api/health").json() == {"status": "ok", "version": "0.3.0"}


def test_frontend_update_changes_module_graph_url(client, tmp_path, monkeypatch):
    from app import application

    def frontend_path(response):
        assert response.headers["Cache-Control"] == "no-cache"
        return re.search(r'src="(/frontend/[a-f0-9]+)/app\.js"', response.text)[1]

    original = frontend_path(client.get("/"))
    assert client.get(f"{original}/app.js").status_code == 200
    assert client.get(f"{original}/js/shell.js").status_code == 200
    assert client.get(f"{original}/style.css").status_code == 200

    static = tmp_path / "static"
    (static / "js").mkdir(parents=True)
    for name in ("index.html", "app.js"):
        (static / name).write_bytes((application.STATIC / name).read_bytes())
    (static / "js/shell.js").write_text("// Previous navigation", encoding="utf-8")
    monkeypatch.setattr(application, "STATIC", static)
    config = AppConfig(
        tmp_path / "test-data",
        tmp_path / "test-cache",
        "fictional-test-password",
        background_enabled=False,
    )
    with TestClient(create_app(config)) as previous:
        previous_path = frontend_path(previous.get("/"))
    (static / "js/shell.js").write_text("// Updated navigation", encoding="utf-8")
    with TestClient(create_app(config)) as updated:
        assert frontend_path(updated.get("/")) != previous_path


def test_calendar_sync_is_limited_to_three_minutes(monkeypatch):
    now = [1000]
    calls = []
    sync = caldav.CalendarSync(None)
    monkeypatch.setattr(sync, "fetch_and_publish", lambda: calls.append(now[0]))
    monkeypatch.setattr(caldav.time, "monotonic", lambda: now[0])
    sync.sync()
    now[0] += caldav.CALENDAR_SYNC_INTERVAL - 1
    sync.sync()
    assert calls == [1000]
    now[0] += 1
    sync.sync()
    assert calls == [1000, 1000 + caldav.CALENDAR_SYNC_INTERVAL]


def setup_task(c, mode="individual", kind="tasks", members=1):
    people = [
        create(c, "members", {"name": f"Persoon {i}", "color": "#aa7755"})[0]
        for i in range(members)
    ]
    today = c.get("/api/state").json()["day"]
    body = {
        "title": "Testtaak",
        "icon": "✓",
        "date": today,
        "repeat": "daily",
        "mode": mode,
        "members": people,
        "weekdays": list(range(7)),
        "points": 5,
    }
    if kind == "routines":
        body.update(
            steps=[{"text": "Stap één", "icon": "✓"}, {"text": "Stap twee", "icon": "☀"}],
            start_time="07:00",
            end_time="09:00",
        )
    id, result = create(c, kind, body)
    assert result.status_code == 200, result.text
    return id, body, today


def test_member_role_is_saved_and_validated(client):
    child_id, child = create(
        client, "members", {"name": "Alex", "color": "#aa7755", "role": "child"}
    )
    parent_id, parent = create(
        client, "members", {"name": "Sam", "color": "#5577aa", "role": "parent"}
    )
    assert child.status_code == parent.status_code == 200
    members = {member["id"]: member for member in client.get("/api/state").json()["members"]}
    assert members[child_id]["role"] == "child"
    assert members[parent_id]["role"] == "parent"
    assert (
        create(client, "members", {"name": "Invalid", "color": "#ffffff", "role": "grandparent"})[
            1
        ].status_code
        == 422
    )


def test_member_photo_is_served_separately_and_preserved_on_profile_edit(client):
    photo = b"\xff\xd8\xfffake-jpeg-payload"
    encoded = "data:image/jpeg;base64," + base64.b64encode(photo).decode()
    member_id, created = create(
        client,
        "members",
        {"name": "Alex", "color": "#aa7755", "avatar": encoded, "avatar_changed": "true"},
    )
    assert created.status_code == 200

    member = next(m for m in client.get("/api/state").json()["members"] if m["id"] == member_id)
    assert member["avatar"] == ""
    assert member["avatar_url"] == f"/member-avatar/{member_id}/1"
    image = client.get(member["avatar_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert image.content == photo

    _, updated = create(
        client,
        "members",
        {
            "name": "Alex Jansen",
            "color": "#aa7755",
            "avatar": "",
            "avatar_changed": "",
        },
        id=member_id,
        version=1,
    )
    assert updated.status_code == 200
    member = next(m for m in client.get("/api/state").json()["members"] if m["id"] == member_id)
    assert member["avatar_url"] == f"/member-avatar/{member_id}/2"
    assert client.get(member["avatar_url"]).content == photo
    assert encoded not in client.get("/api/history").text
    assert client.get(f"/member-avatar/{member_id}/1").status_code == 404

    _, removed = create(
        client,
        "members",
        {
            "name": "Alex Jansen",
            "color": "#aa7755",
            "avatar": "",
            "avatar_changed": "true",
        },
        id=member_id,
        version=2,
    )
    assert removed.status_code == 200
    member = next(m for m in client.get("/api/state").json()["members"] if m["id"] == member_id)
    assert "avatar_url" not in member
    assert client.get(f"/member-avatar/{member_id}/3").status_code == 404


@pytest.mark.parametrize(
    "avatar",
    [
        "data:image/svg+xml;base64,PHN2Zz4=",
        "data:image/jpeg;base64,dGVzdA==",
        "data:image/jpeg;base64," + "A" * 220_001,
    ],
)
def test_invalid_member_photos_are_rejected(client, avatar):
    _, result = create(
        client,
        "members",
        {"name": "Alex", "color": "#aa7755", "avatar": avatar, "avatar_changed": "true"},
    )
    assert result.status_code == 422


def test_admin_and_secret_isolation(client):
    cfg = client.get("/api/admin/settings").json()
    cfg.update(immich_url="http://immich.example.org", immich_key="TOPSECRET")
    assert client.post("/api/admin/settings", json=cfg).status_code == 200
    assert "TOPSECRET" not in client.get("/api/state").text
    assert "TOPSECRET" not in client.get("/api/admin/settings").text
    client.cookies.clear()
    assert client.get("/api/admin/settings").status_code == 401
    assert create(client, "members", {"name": "No", "color": "#ffffff"})[1].status_code == 401
    assert client.post("/api/admin/sync").status_code == 401


def test_public_dashboard_refresh_does_not_change_admin_session(client):
    auth_runtime = client.app.state.runtime.auth
    original_expiry = auth_runtime.sessions["test-admin"]

    for _ in range(5):
        assert client.get("/api/state").status_code == 200

    assert auth_runtime.sessions["test-admin"] == original_expiry
    assert client.get("/api/admin/settings").status_code == 200


def test_branding_settings_are_saved_and_publicly_served(client):
    cfg = client.get("/api/admin/settings").json()
    assert cfg["brand_title"] == "samen"
    assert cfg["brand_subtitle"] == "een plek voor ons allemaal"
    assert cfg["brand_image"] == ""
    cfg.update(
        brand_title="Familie Jansen",
        brand_subtitle="Samen thuis",
        brand_image="data:image/jpeg;base64,/9j/",
    )
    assert client.post("/api/admin/settings", json=cfg).status_code == 200

    state = client.get("/api/state").json()
    assert state["config"]["brand_title"] == "Familie Jansen"
    assert state["config"]["brand_subtitle"] == "Samen thuis"
    assert state["config"]["brand_image"] is True
    image = client.get(f"/brand-image/{state['config']['brand_version']}")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert image.content == b"\xff\xd8\xff"
    assert client.get("/brand-image/0").status_code == 404


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("brand_title", "x" * 41),
        ("brand_subtitle", "x" * 81),
        ("brand_image", "data:image/svg+xml;base64,PHN2Zz4="),
        ("brand_image", "data:image/jpeg;base64,dGVzdA=="),
    ],
)
def test_invalid_branding_settings_are_rejected(client, field, value):
    cfg = client.get("/api/admin/settings").json()
    cfg[field] = value
    assert client.post("/api/admin/settings", json=cfg).status_code == 422


def test_cross_origin_rejected(client):
    assert client.post("/api/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    with TestClient(client.app) as c:
        assert c.post("/api/logout").status_code == 403


def test_request_body_limit_rejects_large_content_length(client):
    response = client.post(
        "/api/logout",
        content=b"x" * (security.MAX_REQUEST_BODY_BYTES + 1),
        headers={**HEAD, "Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Verzoek is te groot."}


def test_request_body_limit_rejects_oversized_stream_without_content_length():
    middleware = security.RequestBodyLimitMiddleware(
        lambda *args: pytest.fail("Oversized body reached the application"), 4
    )
    messages = iter(
        [
            {"type": "http.request", "body": b"123", "more_body": True},
            {"type": "http.request", "body": b"456", "more_body": False},
        ]
    )
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    asyncio.run(
        middleware(
            {"type": "http", "method": "POST", "path": "/api/login", "headers": []},
            receive,
            send,
        )
    )
    assert sent[0]["status"] == 413


def test_login_rate_limit_is_shared_across_ip_addresses(client, monkeypatch):
    authentication = client.app.state.runtime.auth
    for index in range(auth.LOGIN_BURST):
        request = Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/api/login",
                "raw_path": b"/api/login",
                "query_string": b"",
                "headers": [],
                "client": (f"192.0.2.{index + 1}", 1234),
                "server": ("testserver", 80),
            }
        )
        with pytest.raises(HTTPException) as error:
            authentication.login(Login(password="incorrect"), request, Response())
        assert error.value.status_code == 401

    with db.connect() as connection:
        assert connection.execute("SELECT tokens FROM login_limiter WHERE id=1").fetchone()[0] < 1
    with authentication.login_lock:
        authentication.attempts.clear()

    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/login",
            "raw_path": b"/api/login",
            "query_string": b"",
            "headers": [],
            "client": ("192.0.2.99", 1234),
            "server": ("testserver", 80),
        }
    )
    with pytest.raises(HTTPException) as error:
        authentication.login(Login(password="incorrect"), request, Response())
    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"]


def test_backup_is_created_with_private_permissions(client, tmp_path):
    destination = tmp_path / "family-backup.db"
    backup.create_backup(destination, db.DATA / "family.db")
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    with sqlite3.connect(destination) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(FileExistsError):
        backup.create_backup(destination, db.DATA / "family.db")


def test_environment_loader_reads_dotenv_without_overriding_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ADMIN_PASSWORD=fixture-password\n")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    load_environment(env_file)
    assert os.environ["ADMIN_PASSWORD"] == "fixture-password"
    monkeypatch.setenv("ADMIN_PASSWORD", "already-set")
    load_environment(env_file)
    assert os.environ["ADMIN_PASSWORD"] == "already-set"


def test_groceries_idempotency_conflict_and_restore(client):
    rid = str(uuid.uuid4())
    id, r = create(client, "groceries", {"name": "Appels"}, request_id=rid)
    assert r.status_code == 200
    assert (
        create(client, "groceries", {"name": "Appels"}, id=id, request_id=rid)[1].status_code == 200
    )
    assert len(client.get("/api/state").json()["groceries"]) == 1
    assert (
        create(client, "groceries", {"name": "Peren"}, id=id, request_id=rid)[1].status_code == 409
    )
    assert (
        create(client, "groceries", {"name": "Appels", "done": True}, id=id, version=1)[
            1
        ].status_code
        == 200
    )
    assert create(client, "groceries", {"name": "Anders"}, id=id, version=1)[1].status_code == 409
    assert (
        create(client, "groceries", {"name": "Appels", "done": False}, id=id, version=2)[
            1
        ].status_code
        == 200
    )
    assert client.get("/api/state").json()["groceries"][0]["done"] is False


def test_simultaneous_task_completion_one_history_entry(client):
    setup_task(client, mode="shared", members=2)
    run = client.get("/api/state").json()["runs"][0]

    def complete(_):
        return create(client, "runs", {"done": [0]}, id=run["id"], version=1)[1].status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(complete, range(2))) == [200, 200]
    runs = client.get("/api/state").json()["runs"]
    assert len(runs) == 1 and runs[0]["done"] == [0] and runs[0]["version"] == 2
    history = client.get("/api/history").json()
    assert len([h for h in history if h["kind"] == "runs"]) == 1


def test_task_points_are_idempotent_and_undo_creates_a_reversal(client):
    task_id, _, _ = setup_task(client)
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = next(r for r in state["runs"] if r["template_id"] == task_id)
    payload = {"done": [0]}
    first = create(client, "runs", payload, id=run["id"], version=run["version"])[1]
    assert first.status_code == 200
    assert client.get("/api/state").json()["balances"][member_id] == {
        "balance": 5,
        "reserved": 0,
        "available": 5,
    }

    duplicate = create(client, "runs", payload, id=run["id"], version=run["version"])[1]
    assert duplicate.status_code == 200
    with db.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM point_transactions").fetchone()[0] == 1

    updated = next(r for r in client.get("/api/state").json()["runs"] if r["id"] == run["id"])
    assert (
        create(client, "runs", {"done": []}, id=run["id"], version=updated["version"])[
            1
        ].status_code
        == 200
    )
    state = client.get("/api/state").json()
    assert state["balances"][member_id]["balance"] == 0
    assert sorted(t["amount"] for t in state["point_transactions"]) == [-5, 5]

    reopened = next(r for r in state["runs"] if r["id"] == run["id"])
    assert (
        create(client, "runs", payload, id=run["id"], version=reopened["version"])[1].status_code
        == 200
    )
    assert client.get("/api/state").json()["balances"][member_id]["balance"] == 5


def test_shared_task_awards_each_assigned_member_once(client):
    setup_task(client, mode="shared", members=2)
    state = client.get("/api/state").json()
    run = state["runs"][0]
    assert run["member"] == "shared"
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    state = client.get("/api/state").json()
    assert [state["balances"][m["id"]]["balance"] for m in state["members"]] == [5, 5]
    assert len([t for t in state["point_transactions"] if t["reason"] == "completion"]) == 2


def test_routine_awards_only_once_when_all_steps_are_done_and_reverses_on_undo(client):
    setup_task(client, kind="routines")
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = state["runs"][0]
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    assert client.get("/api/state").json()["balances"][member_id]["balance"] == 0
    run = next(r for r in client.get("/api/state").json()["runs"] if r["id"] == run["id"])
    assert (
        create(client, "runs", {"done": [0, 1]}, id=run["id"], version=run["version"])[
            1
        ].status_code
        == 200
    )
    state = client.get("/api/state").json()
    assert state["balances"][member_id]["balance"] == 5
    assert len([t for t in state["point_transactions"] if t["reason"] == "completion"]) == 1
    run = next(r for r in state["runs"] if r["id"] == run["id"])
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    state = client.get("/api/state").json()
    assert state["balances"][member_id]["balance"] == 0
    assert sorted(t["amount"] for t in state["point_transactions"]) == [-5, 5]


def test_reward_request_reserves_points_and_approval_debits_once(client):
    task_id, _, _ = setup_task(client)
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = next(r for r in state["runs"] if r["template_id"] == task_id)
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    reward_id, saved = create(
        client,
        "rewards",
        {
            "title": "Extra schermtijd",
            "description": "Een half uur",
            "icon": "🎮",
            "price": 4,
        },
    )
    assert saved.status_code == 200

    request_payload = {
        "request_id": "reward-request-001",
        "member_id": member_id,
        "reward_id": reward_id,
    }
    requested = client.post("/api/reward-requests", json=request_payload)
    assert requested.status_code == 200
    repeated = client.post("/api/reward-requests", json=request_payload)
    assert repeated.json() == requested.json()
    state = client.get("/api/state").json()
    assert state["balances"][member_id] == {"balance": 5, "reserved": 4, "available": 1}
    assert len(state["reward_requests"]) == 1

    decision_payload = {"request_id": "reward-approve-001", "action": "approve"}
    path = f"/api/admin/reward-requests/{requested.json()['id']}/decision"
    approved = client.post(path, json=decision_payload)
    assert approved.status_code == 200
    assert client.post(path, json=decision_payload).json() == approved.json()
    state = client.get("/api/state").json()
    assert state["balances"][member_id] == {"balance": 1, "reserved": 0, "available": 1}
    assert len([t for t in state["point_transactions"] if t["reason"] == "reward-redemption"]) == 1


def test_admin_points_adjustment_is_idempotent_and_records_reason(client):
    member_id, created = create(client, "members", {"name": "Alex", "color": "#aa7755"})
    assert created.status_code == 200
    payload = {
        "request_id": "points-adjustment-001",
        "member_id": member_id,
        "amount": 3,
        "reason": "Startcorrectie",
    }

    response = client.post("/api/admin/points/adjustments", json=payload)
    assert response.status_code == 200
    assert response.json()["balance"] == 3
    assert client.post("/api/admin/points/adjustments", json=payload).json() == response.json()

    state = client.get("/api/state").json()
    assert state["balances"][member_id] == {"balance": 3, "reserved": 0, "available": 3}
    adjustments = [
        t for t in state["point_transactions"] if t["reason"].startswith("manual-adjustment:")
    ]
    assert len(adjustments) == 1
    assert adjustments[0]["amount"] == 3
    assert adjustments[0]["reason"] == "manual-adjustment:Startcorrectie"

    changed_payload = payload | {"amount": 4}
    assert client.post("/api/admin/points/adjustments", json=changed_payload).status_code == 409
    assert (
        client.post(
            "/api/admin/points/adjustments",
            json=payload | {"amount": 0, "request_id": "points-adjustment-002"},
        ).status_code
        == 422
    )
    without_reason = client.post(
        "/api/admin/points/adjustments",
        json={
            "request_id": "points-adjustment-003",
            "member_id": member_id,
            "amount": 1,
        },
    )
    assert without_reason.status_code == 200
    transaction = next(
        t
        for t in client.get("/api/state").json()["point_transactions"]
        if t["id"] == without_reason.json()["id"]
    )
    assert transaction["reason"] == "manual-adjustment"


def test_points_adjustment_protects_reserved_reward_points(client):
    _, _, _ = setup_task(client)
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = state["runs"][0]
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    reward_id, created = create(client, "rewards", {"title": "Sticker", "price": 4})
    assert created.status_code == 200
    requested = client.post(
        "/api/reward-requests",
        json={
            "request_id": "reserve-for-adjustment",
            "member_id": member_id,
            "reward_id": reward_id,
        },
    )
    assert requested.status_code == 200

    route = "/api/admin/points/adjustments"
    payload = {
        "request_id": "points-adjustment-reserved",
        "member_id": member_id,
        "amount": -2,
        "reason": "Correctie",
    }
    assert client.post(route, json=payload).status_code == 409
    allowed = client.post(
        route, json=payload | {"request_id": "points-adjustment-allowed", "amount": -1}
    )
    assert allowed.status_code == 200
    assert client.get("/api/state").json()["balances"][member_id] == {
        "balance": 4,
        "reserved": 4,
        "available": 0,
    }


def test_points_adjustment_requires_admin(client):
    client.cookies.delete("family_admin")
    response = client.post(
        "/api/admin/points/adjustments",
        json={
            "request_id": "points-adjustment-no-admin",
            "member_id": str(uuid.uuid4()),
            "amount": 5,
            "reason": "Test",
        },
    )
    assert response.status_code == 401


def test_pending_reward_requests_reserve_balance_and_rejection_releases_it(client):
    _, _, _ = setup_task(client)
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = state["runs"][0]
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    reward_id, result = create(client, "rewards", {"title": "Sticker", "price": 3})
    assert result.status_code == 200
    payload = {"request_id": "reward-pending-001", "member_id": member_id, "reward_id": reward_id}
    requested = client.post("/api/reward-requests", json=payload)
    assert requested.status_code == 200
    assert (
        client.post(
            "/api/reward-requests", json={**payload, "request_id": "reward-pending-002"}
        ).status_code
        == 409
    )
    path = f"/api/admin/reward-requests/{requested.json()['id']}/decision"
    rejected = client.post(path, json={"request_id": "reward-reject-001", "action": "reject"})
    assert rejected.status_code == 200
    assert client.get("/api/state").json()["balances"][member_id] == {
        "balance": 5,
        "reserved": 0,
        "available": 5,
    }


def test_concurrent_reward_requests_cannot_reserve_the_same_points_twice(client):
    _, _, _ = setup_task(client)
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = state["runs"][0]
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    reward_id, result = create(client, "rewards", {"title": "Kaartje", "price": 4})
    assert result.status_code == 200

    def request(number):
        return client.post(
            "/api/reward-requests",
            json={
                "request_id": f"concurrent-reward-{number:02}",
                "member_id": member_id,
                "reward_id": reward_id,
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(request, range(2))) == [200, 409]
    state = client.get("/api/state").json()
    assert len(state["reward_requests"]) == 1
    assert state["balances"][member_id] == {"balance": 5, "reserved": 4, "available": 1}


def test_reward_decisions_require_admin(client):
    _, _, _ = setup_task(client)
    state = client.get("/api/state").json()
    member_id = state["members"][0]["id"]
    run = state["runs"][0]
    assert (
        create(client, "runs", {"done": [0]}, id=run["id"], version=run["version"])[1].status_code
        == 200
    )
    reward_id, result = create(client, "rewards", {"title": "Boek", "price": 1})
    assert result.status_code == 200
    requested = client.post(
        "/api/reward-requests",
        json={
            "request_id": "auth-reward-request",
            "member_id": member_id,
            "reward_id": reward_id,
        },
    )
    assert requested.status_code == 200
    client.cookies.clear()
    decision = client.post(
        f"/api/admin/reward-requests/{requested.json()['id']}/decision",
        json={"request_id": "unauthorized-reward-decision", "action": "approve"},
    )
    assert decision.status_code == 401


def test_reward_catalog_is_admin_only_and_price_is_validated(client):
    client.cookies.clear()
    reward_id = str(uuid.uuid4())
    payload = {
        "request_id": str(uuid.uuid4()),
        "id": reward_id,
        "version": 0,
        "body": {"title": "Beloning", "price": 0},
    }
    assert client.post("/api/entities/rewards", json=payload).status_code == 401
    client.cookies.set("family_admin", "test-admin")
    assert client.post("/api/entities/rewards", json=payload).status_code == 422


def test_v1_database_migrates_to_reward_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA", tmp_path)
    with sqlite3.connect(tmp_path / "family.db") as connection:
        connection.execute(
            "CREATE TABLE settings (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, body TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO settings VALUES (1,1,?)",
            (
                json.dumps(
                    {
                        "timezone": "Europe/Amsterdam",
                        "caldav": [],
                        "ha_url": "",
                        "ha_dashboard": "/lovelace/0",
                        "immich_url": "",
                        "immich_key": "",
                        "albums": [],
                        "slide_seconds": 15,
                    }
                ),
            ),
        )
        connection.execute("PRAGMA user_version=1")
    db.init()
    with db.connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name='point_transactions'"
        ).fetchone()
        assert db.settings(connection)["timezone"] == "Europe/Amsterdam"


def test_individual_tasks_and_routine_new_day(client):
    setup_task(client, members=2)
    _, _, today = setup_task(client, kind="routines", members=2)
    runs = client.get("/api/state").json()["runs"]
    assert len(runs) == 4
    run = next(r for r in runs if r["kind"] == "routines")
    assert create(client, "runs", {"done": [0]}, id=run["id"], version=1)[1].status_code == 200
    assert next(r for r in client.get("/api/state").json()["runs"] if r["id"] == run["id"])[
        "done"
    ] == [0]
    tomorrow = (datetime.fromisoformat(today) + timedelta(days=1)).date().isoformat()
    assert all(
        r["done"] == [] for r in client.get("/api/state", params={"day": tomorrow}).json()["runs"]
    )
    assert next(r for r in client.get("/api/state").json()["runs"] if r["id"] == run["id"])[
        "done"
    ] == [0]


def test_week_state_includes_local_task_occurrences_without_caldav(client):
    _, body, today = setup_task(client)
    current = datetime.fromisoformat(today).date()
    monday = current - timedelta(days=current.weekday())
    body["date"] = monday.isoformat()
    task_id, saved = create(client, "tasks", body)
    assert saved.status_code == 200
    state = client.get("/api/state", params={"day": today, "period": "week"})
    assert state.status_code == 200
    result = state.json()
    occurrences = [r for r in result["runs"] if r["template_id"] == task_id]
    assert len(occurrences) == 7
    assert {r["day"] for r in occurrences} == {
        (monday + timedelta(days=offset)).isoformat() for offset in range(7)
    }
    assert result["events"] == []
    assert result["config"]["caldav_configured"] is False


def test_three_day_state_includes_today_and_two_following_days(client):
    task_id, _, today = setup_task(client)
    state = client.get("/api/state", params={"day": today, "period": "three-day"})
    assert state.status_code == 200
    occurrences = [run for run in state.json()["runs"] if run["template_id"] == task_id]
    assert len(occurrences) == 3
    assert {run["day"] for run in occurrences} == {
        (date.fromisoformat(today) + timedelta(days=offset)).isoformat() for offset in range(3)
    }


def test_state_rejects_unknown_calendar_period(client):
    today = client.get("/api/state").json()["day"]
    assert client.get("/api/state", params={"day": today, "period": "month"}).status_code == 422


def test_routine_concurrent_different_steps_conflict(client):
    setup_task(client, kind="routines")
    run = client.get("/api/state").json()["runs"][0]
    assert create(client, "runs", {"done": [0]}, id=run["id"], version=1)[1].status_code == 200
    assert create(client, "runs", {"done": [1]}, id=run["id"], version=1)[1].status_code == 409
    assert create(client, "runs", {"done": [0, 1]}, id=run["id"], version=2)[1].status_code == 200


@pytest.mark.parametrize(
    "original_mode,new_mode,count", [("individual", "shared", 1), ("shared", "individual", 2)]
)
def test_task_mode_edit_hides_superseded_untouched_runs(client, original_mode, new_mode, count):
    task_id, body, today = setup_task(client, mode=original_mode, members=2)
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    old_runs = client.get("/api/state", params={"day": tomorrow}).json()["runs"]
    assert (
        create(client, "tasks", {**body, "mode": new_mode}, id=task_id, version=1)[1].status_code
        == 200
    )

    for day in (today, tomorrow):
        for _ in range(2):  # Polling must not bring back the superseded executions.
            runs = client.get("/api/state", params={"day": day}).json()["runs"]
            assert len(runs) == count
            assert all(run["body"]["mode"] == new_mode for run in runs)
    with db.connect() as connection:
        for run in old_runs:
            stored = connection.execute("SELECT * FROM runs WHERE id=?", (run["id"],)).fetchone()
            assert json.loads(stored["body"]) == run["body"]
            assert stored["version"] == run["version"]

    # An earlier day without replacement executions keeps its original snapshots.
    earlier = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    with db.connect() as connection:
        connection.execute("UPDATE runs SET day=? WHERE id=?", (earlier, old_runs[0]["id"]))
    historical = client.get("/api/state", params={"day": earlier}).json()["runs"]
    assert [run["id"] for run in historical] == [old_runs[0]["id"]]


@pytest.mark.parametrize("undo", [False, True])
def test_task_mode_edit_preserves_executions_with_completion_history(client, undo):
    task_id, body, _ = setup_task(client)
    run = client.get("/api/state").json()["runs"][0]
    assert create(client, "runs", {"done": [0]}, id=run["id"], version=1)[1].status_code == 200
    if undo:
        assert create(client, "runs", {"done": []}, id=run["id"], version=2)[1].status_code == 200
    before = client.get("/api/state").json()
    assert (
        create(client, "tasks", {**body, "mode": "shared"}, id=task_id, version=1)[1].status_code
        == 200
    )
    after = client.get("/api/state").json()
    if undo:
        assert [item["member"] for item in after["runs"]] == ["shared"]
    else:
        assert before["runs"][0] in after["runs"]
    with db.connect() as connection:
        stored = connection.execute("SELECT * FROM runs WHERE id=?", (run["id"],)).fetchone()
        assert json.loads(stored["done"]) == before["runs"][0]["done"]
        assert stored["version"] == before["runs"][0]["version"]
    assert after["balances"] == before["balances"]
    assert after["point_transactions"] == before["point_transactions"]


def test_template_edits_preserve_snapshot(client):
    id, body, today = setup_task(client)
    old = client.get("/api/state").json()["runs"][0]
    assert (
        create(client, "tasks", {**body, "title": "Nieuwe titel"}, id=id, version=1)[1].status_code
        == 200
    )
    assert client.get("/api/state").json()["runs"][0]["body"]["title"] == old["body"]["title"]
    assert (
        create(client, "tasks", {**body, "archived": True}, id=id, version=2)[1].status_code == 200
    )
    tomorrow = (datetime.fromisoformat(today) + timedelta(days=1)).date().isoformat()
    assert not client.get("/api/state", params={"day": tomorrow}).json()["runs"]


def test_sqlite_backup_restore(client, tmp_path, monkeypatch):
    create(client, "groceries", {"name": "Brood", "quantity": "2 stuks"})
    cfg = client.get("/api/admin/settings").json()
    cfg["immich_key"] = "backup-secret"
    client.post("/api/admin/settings", json=cfg)
    restored = tmp_path / "restored"
    restored.mkdir()
    with (
        sqlite3.connect(db.DATA / "family.db") as source,
        sqlite3.connect(restored / "family.db") as dest,
    ):
        source.backup(dest)
    monkeypatch.setattr(db, "DATA", restored)
    db.init()
    restored_config = AppConfig(
        restored, tmp_path / "restored-cache", "test", background_enabled=False
    )
    with TestClient(create_app(restored_config)) as restored_client:
        assert restored_client.get("/api/state").json()["groceries"][0]["name"] == "Brood"
    with db.connect() as c:
        assert db.settings(c)["immich_key"] == "backup-secret"


def test_future_schema_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA", tmp_path)
    with sqlite3.connect(tmp_path / "family.db") as c:
        c.execute("PRAGMA user_version=999")
    with pytest.raises(RuntimeError):
        db.init()


def test_photo_permission_error_is_actionable(client, monkeypatch):
    import httpx

    pid = str(uuid.uuid4())
    monkeypatch.setattr(client.app.state.runtime.photos, "assets", {pid: {"id": pid}})
    response = httpx.Response(403, request=httpx.Request("GET", "http://immich.example.org"))
    monkeypatch.setattr(immich, "immich_get", lambda *args: response)
    monkeypatch.setattr(client.app.state.runtime.photos, "cache", db.DATA.parent / "cache")
    result = client.get("/api/photos/" + pid)
    assert result.status_code == 403
    assert "asset.view" in result.json()["detail"]


def test_unselected_photo_never_requested(client, monkeypatch):
    monkeypatch.setattr(
        immich, "immich_get", lambda *a: pytest.fail("Must not request arbitrary photos")
    )
    assert client.get("/api/photos/unknown").status_code == 404


def test_ical_dst_exception_all_day():
    raw = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//NL
BEGIN:VEVENT
UID:recurrence
DTSTART;TZID=Europe/Amsterdam:20261024T090000
DTEND;TZID=Europe/Amsterdam:20261024T100000
RRULE:FREQ=DAILY;COUNT=3
EXDATE;TZID=Europe/Amsterdam:20261025T090000
SUMMARY:Origineel
END:VEVENT
BEGIN:VEVENT
UID:recurrence
RECURRENCE-ID;TZID=Europe/Amsterdam:20261026T090000
DTSTART;TZID=Europe/Amsterdam:20261026T110000
DTEND;TZID=Europe/Amsterdam:20261026T120000
SUMMARY:Verplaatst
END:VEVENT
BEGIN:VEVENT
UID:all-day
DTSTART;VALUE=DATE:20261025
DTEND;VALUE=DATE:20261027
SUMMARY:Hele dag
END:VEVENT
END:VCALENDAR"""
    tz = ZoneInfo("Europe/Amsterdam")
    events = caldav.expand_ics(
        raw, datetime(2026, 10, 23, tzinfo=tz), datetime(2026, 10, 28, tzinfo=tz), tz
    )
    assert len(events) == 3
    assert (
        next(e for e in events if e["title"] == "Origineel")["start"] == "2026-10-24T09:00:00+02:00"
    )
    assert (
        next(e for e in events if e["title"] == "Verplaatst")["start"]
        == "2026-10-26T11:00:00+01:00"
    )
    assert next(e for e in events if e["title"] == "Hele dag")["all_day"] is True


def test_missed_days_materialized_before_template_edit(client):
    id, body, today = setup_task(client)
    earlier = (datetime.fromisoformat(today) - timedelta(days=2)).date().isoformat()
    # Simulate a template saved before a server was offline for two days.
    with db.connect() as c:
        stored = {**body, "date": earlier}
        c.execute("UPDATE entities SET body=? WHERE id=?", (json.dumps(stored), id))
        c.execute("DELETE FROM schedule_cursor WHERE id=?", (id,))
    assert (
        create(client, "tasks", {**stored, "title": "Updated"}, id=id, version=1)[1].status_code
        == 200
    )
    with db.connect() as c:
        runs = c.execute("SELECT * FROM runs WHERE template_id=?", (id,)).fetchall()
        assert len(runs) == 3
        assert all(
            json.loads(r["body"])["title"] == "Testtaak" and json.loads(r["done"]) == []
            for r in runs
        )


def test_caldav_atomic_replacement_and_failure_keeps_cache(client, monkeypatch):
    # Use the real sync function despite the fixture disabling background network work.
    from types import SimpleNamespace

    real = caldav
    synchronizer = client.app.state.runtime.calendars
    now = [1000]
    monkeypatch.setattr(synchronizer, "last_sync", None)
    monkeypatch.setattr(real.time, "monotonic", lambda: now[0])
    account = {
        "id": str(uuid.uuid4()),
        "url": "http://calendar.example.org",
        "username": "test",
        "password": "secret",
        "calendars": [{"url": "http://calendar.example.org/a/", "name": "Gezin", "member": ""}],
    }
    with db.connect() as c:
        cfg = db.settings(c)
        cfg["caldav"] = [account]
        c.execute("UPDATE settings SET body=?", (json.dumps(cfg),))
    raw = "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nUID:demo\nDTSTART:20261030T090000Z\nDTEND:20261030T100000Z\nSUMMARY:Afspraak\nEND:VEVENT\nEND:VCALENDAR"
    resources = [SimpleNamespace(data=raw)]

    class Fake:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def principal(self):
            return self

        def calendars(self):
            return [self]

        url = "http://calendar.example.org/a/"

        def search(self, **kwargs):
            return resources

    monkeypatch.setattr(real, "client", lambda a: Fake())

    def sync_after_interval():
        now[0] += real.CALENDAR_SYNC_INTERVAL
        synchronizer.sync()

    synchronizer.sync()
    state = client.get("/api/state").json()
    assert len(state["events"]) == 1
    calendar_status = state["status"]["caldav:" + account["id"]]
    assert calendar_status["calendars"] == [{"name": "Gezin"}]
    assert calendar_status["last_success"]
    resources[:] = [SimpleNamespace(data=raw.replace("Afspraak", "Gewijzigd"))]
    sync_after_interval()
    state = client.get("/api/state").json()
    assert state["events"][0]["title"] == "Gewijzigd"
    last_success = state["status"]["caldav:" + account["id"]]["last_success"]
    monkeypatch.setattr(
        real, "client", lambda a: (_ for _ in ()).throw(OSError("private server data"))
    )
    sync_after_interval()
    state = client.get("/api/state").json()
    assert len(state["events"]) == 1 and state["status"]["caldav:" + account["id"]]["ok"] is False
    assert state["status"]["caldav:" + account["id"]]["last_success"] == last_success
    assert state["status"]["caldav:" + account["id"]]["calendars"] == [{"name": "Gezin"}]
    assert "private server data" not in json.dumps(state)
    monkeypatch.setattr(real, "client", lambda a: Fake())
    resources.clear()
    sync_after_interval()
    assert client.get("/api/state").json()["events"] == []


def test_immich_album_revocation_and_bounded_cache(client, monkeypatch):
    import httpx

    aid = str(uuid.uuid4())
    pid = str(uuid.uuid4())
    with db.connect() as c:
        cfg = db.settings(c)
        cfg.update(immich_url="http://immich.example.org", immich_key="secret", albums=[aid])
        c.execute("UPDATE settings SET body=?", (json.dumps(cfg),))
    response = {"albumName": "Testalbum", "assets": [{"id": pid, "type": "IMAGE"}]}

    def fake_get(cfg, path):
        return httpx.Response(
            200, json=response, request=httpx.Request("GET", "http://immich.example.org")
        )

    monkeypatch.setattr(immich, "immich_get", fake_get)
    real_sync = client.app.state.runtime.photos.sync
    monkeypatch.setattr(client.app.state.runtime.photos, "cache", db.DATA.parent / "cache")
    monkeypatch.setattr(immich, "immich_get", fake_get)
    real_sync()
    assert pid in client.app.state.runtime.photos.assets
    path = client.app.state.runtime.photos.cache / hashlib.sha256(pid.encode()).hexdigest()
    path.write_bytes(b"test-cache")
    response["assets"] = []
    real_sync()
    assert pid not in client.app.state.runtime.photos.assets and not path.exists()
    assert client.get("/api/photos/" + pid).status_code == 404
    monkeypatch.setattr(client.app.state.runtime.photos, "cache_limit", 5)
    client.app.state.runtime.photos.assets = {"a": {}, "b": {}}
    for id in ("a", "b"):
        (
            client.app.state.runtime.photos.cache / hashlib.sha256(id.encode()).hexdigest()
        ).write_bytes(b"1234")
    client.app.state.runtime.photos.purge_cache()
    assert sum(p.stat().st_size for p in client.app.state.runtime.photos.cache.iterdir()) <= 5


@pytest.mark.parametrize("denied_page", [None, 2])
def test_immich_metadata_only_albums_paginate_and_fail_closed(client, monkeypatch, denied_page):
    import httpx

    aid, first, second = (str(uuid.uuid4()) for _ in range(3))
    with db.connect() as c:
        cfg = db.settings(c)
        cfg.update(immich_url="http://immich.example.org", immich_key="secret", albums=[aid])
        c.execute("UPDATE settings SET body=?", (json.dumps(cfg),))
    request = httpx.Request("GET", cfg["immich_url"])
    monkeypatch.setattr(
        immich,
        "immich_get",
        lambda *args: httpx.Response(
            200, json={"albumName": "Nieuw album", "assetCount": 2}, request=request
        ),
    )
    pages = []

    def search(url, *, headers, json, **kwargs):
        assert url.endswith("/api/search/metadata")
        assert json["albumIds"] == [aid] and json["type"] == "IMAGE"
        page = json["page"]
        pages.append(page)
        if page == denied_page:
            return httpx.Response(403, request=request)
        return httpx.Response(
            200,
            json={
                "assets": {
                    "items": [{"id": first if page == 1 else second, "type": "IMAGE"}],
                    "nextPage": "2" if page == 1 else None,
                }
            },
            request=request,
        )

    monkeypatch.setattr(immich.httpx, "post", search)
    monkeypatch.setattr(client.app.state.runtime.photos, "cache", db.DATA.parent / "cache")
    client.app.state.runtime.photos.sync()
    assert pages == [1, 2]
    state = client.get("/api/state").json()
    if denied_page:
        assert state["photos"] == []
        assert state["status"]["immich"]["ok"] is False
        assert "asset.read" in state["status"]["immich"]["message"]
    else:
        assert {p["id"] for p in state["photos"]} == {first, second}
        assert state["status"]["immich"]["ok"] is True


def test_untrusted_entity_ids_rejected(client):
    assert create(client, "groceries", {"name": "Test"}, id='"><img src=x>')[1].status_code == 422


def test_ha_dashboard_settings_are_saved_without_legacy_credentials(client):
    cfg = client.get("/api/admin/settings").json()
    assert cfg["ha_dashboard"] == "/lovelace/0"
    cfg.update(
        ha_url="http://ha.example.org:8123",
        ha_dashboard="/dashboard-family/overview",
        ha_token="old-secret",
        ha_entities=["light.kitchen"],
    )
    assert client.post("/api/admin/settings", json=cfg).status_code == 200
    assert client.get("/api/state").json()["config"]["ha_dashboard"] == "/dashboard-family/overview"
    saved = client.get("/api/admin/settings").json()
    assert saved["ha_dashboard"] == "/dashboard-family/overview"
    assert "ha_token" not in saved and "ha_entities" not in saved
    with db.connect() as connection:
        assert "ha_token" not in db.settings(connection) and "ha_entities" not in db.settings(
            connection
        )
    assert client.get("/api/ha/states").status_code == 404
    assert (
        client.post(
            "/api/ha/control", json={"entity_id": "light.kitchen", "action": "turn_on"}
        ).status_code
        == 404
    )


def test_legacy_ha_credentials_are_removed_on_database_init(client):
    with db.connect() as connection:
        body = json.loads(connection.execute("SELECT body FROM settings WHERE id=1").fetchone()[0])
        body.update(ha_token="old-secret", ha_entities=["light.kitchen"])
        connection.execute("UPDATE settings SET body=? WHERE id=1", (json.dumps(body),))
    db.init()
    with db.connect() as connection:
        stored = json.loads(
            connection.execute("SELECT body FROM settings WHERE id=1").fetchone()[0]
        )
    assert "ha_token" not in stored and "ha_entities" not in stored


@pytest.mark.parametrize(
    "field,value",
    [
        ("ha_url", "http://ha.example.org/lovelace/0"),
        ("ha_url", "http://ha.example.org:invalid"),
        ("ha_dashboard", "//other.example.org/dashboard"),
        ("ha_dashboard", "/lovelace/0?token=secret"),
        ("ha_dashboard", "/../admin"),
        ("ha_dashboard", "https://other.example.org"),
    ],
)
def test_invalid_ha_dashboard_configuration_rejected(client, field, value):
    cfg = client.get("/api/admin/settings").json()
    cfg["ha_url"] = "http://ha.example.org:8123"
    cfg[field] = value
    assert client.post("/api/admin/settings", json=cfg).status_code == 422


@pytest.mark.parametrize("service", ["caldav", "immich"])
def test_changed_endpoint_never_receives_saved_credentials(client, monkeypatch, service):
    old, new = "https://first.example.test", "https://second.example.test"
    cfg = client.get("/api/admin/settings").json()
    account = {
        "id": str(uuid.uuid4()),
        "username": "test",
        "url": old,
        "password": "private",
        "calendars": [],
    }
    cfg.update(caldav=[account], immich_url=old, immich_key="private")
    assert client.post("/api/admin/settings", json=cfg).status_code == 200

    def unexpected(*args):
        pytest.fail("Discovery must reject the change before making a network call")

    monkeypatch.setattr(
        caldav if service == "caldav" else immich,
        "discover" if service == "caldav" else "albums",
        unexpected,
    )
    discover = client.post("/api/admin/discover/" + service, json={"id": account["id"], "url": new})
    assert discover.status_code == 422
    cfg = client.get("/api/admin/settings").json()
    if service == "caldav":
        cfg["caldav"][0]["url"] = new
    else:
        cfg["immich_url"] = new
    assert client.post("/api/admin/settings", json=cfg).status_code == 422
    with db.connect() as connection:
        current = db.settings(connection)
        assert (current["caldav"][0]["url"], current["caldav"][0]["password"]) == (old, "private")
        assert (current["immich_url"], current["immich_key"]) == (old, "private")


def test_future_unstarted_routine_follows_edits_and_rejects_stale_completion(client):
    routine_id, body, today = setup_task(client, kind="routines")
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    original_today = client.get("/api/state").json()["runs"][0]
    planned = client.get("/api/state", params={"day": tomorrow}).json()["runs"][0]
    changed = body | {
        "title": "Naar bed",
        "start_time": "18:30",
        "end_time": "19:30",
        "steps": [{"text": "Tanden poetsen"}, {"text": "Boekje lezen"}, {"text": "Slapen"}],
    }
    assert create(client, "routines", changed, id=routine_id, version=1)[1].status_code == 200
    # An old open agenda must not apply an old step index to the changed routine.
    assert (
        create(client, "runs", {"done": [0]}, id=planned["id"], version=planned["version"])[
            1
        ].status_code
        == 409
    )
    fresh = client.get("/api/state", params={"day": tomorrow}).json()["runs"][0]
    assert fresh["id"] == planned["id"] and fresh["done"] == []
    assert fresh["body"]["title"] == "Naar bed"
    assert fresh["body"]["start_time"] == "18:30" and len(fresh["body"]["steps"]) == 3
    assert fresh["version"] > planned["version"]
    assert client.get("/api/state").json()["runs"][0] == original_today
    assert client.get("/api/state", params={"day": tomorrow}).json()["runs"][0] == fresh
    # A refresh version is not completion history: a later edit must still apply.
    assert (
        create(client, "routines", changed | {"title": "Avondritme"}, id=routine_id, version=2)[
            1
        ].status_code
        == 200
    )
    later = client.get("/api/state", params={"day": tomorrow}).json()["runs"][0]
    assert later["body"]["title"] == "Avondritme" and later["version"] > fresh["version"]
    assert not [row for row in client.get("/api/history").json() if row["kind"] == "runs"]


@pytest.mark.parametrize("progress", ["partial", "complete", "reopened"])
def test_future_routine_with_completion_history_keeps_snapshot_and_points(client, progress):
    routine_id, body, today = setup_task(client, kind="routines", members=2)
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    runs = client.get("/api/state", params={"day": tomorrow}).json()["runs"]
    protected = runs[0]
    done = [0] if progress == "partial" else [0, 1]
    assert (
        create(client, "runs", {"done": done}, id=protected["id"], version=protected["version"])[
            1
        ].status_code
        == 200
    )
    if progress == "reopened":
        assert (
            create(client, "runs", {"done": []}, id=protected["id"], version=2)[1].status_code
            == 200
        )
    before = client.get("/api/state", params={"day": tomorrow}).json()
    protected = next(run for run in before["runs"] if run["id"] == protected["id"])
    assert (
        create(
            client,
            "routines",
            body | {"title": "Gewijzigd", "steps": [{"text": "Nieuw"}]},
            id=routine_id,
            version=1,
        )[1].status_code
        == 200
    )
    history = client.get("/api/history").json()
    after = client.get("/api/state", params={"day": tomorrow}).json()
    assert next(run for run in after["runs"] if run["id"] == protected["id"]) == protected
    assert (
        next(run for run in after["runs"] if run["id"] == runs[1]["id"])["body"]["title"]
        == "Gewijzigd"
    )
    assert after["balances"] == before["balances"]
    assert after["point_transactions"] == before["point_transactions"]
    assert client.get("/api/history").json() == history
    assert (
        create(client, "routines", body | {"archived": True}, id=routine_id, version=2)[
            1
        ].status_code
        == 200
    )
    assert client.get("/api/state", params={"day": tomorrow}).json()["runs"] == [protected]


@pytest.mark.parametrize("change", ["weekdays", "members", "date", "archived"])
def test_future_unstarted_routine_respects_changed_schedule_without_deleting_snapshots(
    client, change
):
    routine_id, body, today = setup_task(client, kind="routines", members=2)
    tomorrow = date.fromisoformat(today) + timedelta(days=1)
    old = client.get("/api/state", params={"day": str(tomorrow)}).json()["runs"]
    changes = {
        "weekdays": {
            "weekdays": [weekday for weekday in range(7) if weekday != tomorrow.weekday()]
        },
        "members": {"members": [body["members"][1]]},
        "date": {"date": str(tomorrow + timedelta(days=1))},
        "archived": {"archived": True},
    }[change]
    assert (
        create(client, "routines", body | changes, id=routine_id, version=1)[1].status_code == 200
    )
    # A removed future occurrence cannot be completed from an old browser card.
    assert (
        create(client, "runs", {"done": [0]}, id=old[0]["id"], version=old[0]["version"])[
            1
        ].status_code
        == 409
    )
    visible = client.get("/api/state", params={"day": str(tomorrow)}).json()["runs"]
    assert len(visible) == (1 if change == "members" else 0)
    with db.connect() as connection:
        assert all(
            connection.execute("SELECT 1 FROM runs WHERE id=?", (run["id"],)).fetchone()
            for run in old
        )
    assert create(client, "routines", body, id=routine_id, version=2)[1].status_code == 200
    restored = client.get("/api/state", params={"day": str(tomorrow)}).json()["runs"]
    assert {run["id"] for run in restored} == {run["id"] for run in old}
