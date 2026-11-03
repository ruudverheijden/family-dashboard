"""Isolated HTTP contracts for purchases, reservations and durable game sessions."""

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_app import client as isolated_client
from test_app import create

client = isolated_client


def funded_member(client, points=30):
    member_id, response = create(client, "members", {"name": "Alex", "color": "#aa7755"})
    assert response.status_code == 200
    assert (
        client.post(
            "/api/admin/points/adjustments",
            json={
                "request_id": str(uuid.uuid4()),
                "member_id": member_id,
                "amount": points,
                "reason": "Test",
            },
        ).status_code
        == 200
    )
    return member_id


def buy(client, member_id, game="maze", **overrides):
    body = {
        "request_id": str(uuid.uuid4()),
        "member_id": member_id,
        "price": 5,
        "version": 0,
        **overrides,
    }
    return client.post(f"/api/games/{game}/sessions", json=body), body


def move(client, session, value=None, action="move", **overrides):
    return client.post(
        f"/api/game-sessions/{session['id']}/actions",
        json={
            "request_id": str(uuid.uuid4()),
            "version": session["version"],
            "action": action,
            "value": value,
            **overrides,
        },
    )


def test_atomic_purchase_retry_and_resume(client):
    member = funded_member(client)
    response, body = buy(client, member)
    assert response.status_code == 200
    session = response.json()
    assert client.get("/api/state").json()["balances"][member]["available"] == 25
    assert client.get("/api/state").json()["game_sessions"] == [session]
    assert buy(client, member)[0].status_code == 409
    updated = move(client, session, action="stop").json()
    repeated = client.post("/api/games/maze/sessions", json=body).json()
    assert repeated == updated
    assert repeated["status"] == "stopped"
    assert client.get("/api/state").json()["balances"][member]["available"] == 25
    assert client.post("/api/games/orchestra/sessions", json=body).status_code == 409
    assert move(client, updated, "left").status_code == 409


def test_simultaneous_purchases_charge_once(client):
    member = funded_member(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: buy(client, member)[0], range(2)))
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert client.get("/api/state").json()["balances"][member]["available"] == 25


def test_reservations_and_insufficient_balance_are_protected(client):
    member = funded_member(client, 6)
    reward, _ = create(client, "rewards", {"title": "Film", "icon": "🎥", "price": 4})
    assert (
        client.post(
            "/api/reward-requests",
            json={"request_id": str(uuid.uuid4()), "member_id": member, "reward_id": reward},
        ).status_code
        == 200
    )
    assert buy(client, member)[0].status_code == 409
    assert client.get("/api/state").json()["balances"][member]["balance"] == 6
    assert buy(client, str(uuid.uuid4()))[0].status_code == 404


def test_price_auth_validation_conflict_and_purchase_snapshot(client):
    member = funded_member(client)
    client.cookies.clear()
    assert client.post("/api/admin/games/maze", json={"price": 9, "version": 0}).status_code == 401
    client.cookies.set("family_admin", "test-admin")
    for price in [0, -1, 1.5, True, 100001]:
        assert (
            client.post("/api/admin/games/maze", json={"price": price, "version": 0}).status_code
            == 422
        )
    assert client.post("/api/admin/games/maze", json={"price": 9, "version": 0}).status_code == 200
    assert client.post("/api/admin/games/maze", json={"price": 9, "version": 0}).status_code == 409
    assert buy(client, member)[0].status_code == 409
    response, _ = buy(client, member, price=9, version=1)
    assert response.status_code == 200
    assert response.json()["cost"] == 9
    assert client.get("/api/state").json()["balances"][member]["available"] == 21


def test_expiry_is_server_enforced_and_retry_does_not_restart(client):
    member = funded_member(client)
    response, body = buy(client, member)
    session = response.json()
    with client.app.state.runtime.database.connect() as db:
        db.execute("UPDATE game_sessions SET expires_at=?", (time.time() - 1,))
    assert move(client, session, "right").status_code == 409
    assert client.get(f"/api/game-sessions/{session['id']}").json()["status"] == "expired"
    assert client.get("/api/state").json()["game_sessions"] == []
    assert client.post("/api/games/maze/sessions", json=body).json()["status"] == "expired"
    assert buy(client, member)[0].status_code == 200


def test_action_deduplication_stale_versions_and_orchestra_completion(client):
    member = funded_member(client)
    response, _ = buy(client, member, "orchestra")
    session = response.json()
    initial = session.copy()
    request_id = str(uuid.uuid4())
    session = move(client, session, session["board"]["sequence"][0], request_id=request_id).json()
    assert session["board"]["round"] == 2
    assert (
        move(client, initial, initial["board"]["sequence"][0], request_id=request_id).json()
        == session
    )
    assert move(client, initial, 0).status_code == 409
    assert move(client, session, True).status_code == 422
    assert move(client, session, 99).status_code == 422
    session = move(client, session, (session["board"]["sequence"][0] + 1) % 4).json()
    assert session["board"]["round"] == 2 and session["board"]["mistakes"] == 1
    assert session["board"]["feedback"] == "mistake"
    while session["status"] == "active":
        sequence = session["board"]["sequence"][:]
        for value in sequence:
            session = move(client, session, value).json()
            assert session["board"]["feedback"] == ""
    assert session["status"] == "completed"
    assert buy(client, member, "orchestra")[0].status_code == 200


def test_memory_requires_photos_hides_cards_and_completes_one_board(client):
    member = funded_member(client)
    assert buy(client, member, "memory")[0].status_code == 409
    photos = client.app.state.runtime.photos
    with photos.lock:
        photos.assets = {str(i): {"id": str(i), "album": "Fictieve foto’s"} for i in range(6)}
    response, _ = buy(client, member, "memory")
    session = response.json()
    assert session["board"]["cards"] == [None] * 12
    with client.app.state.runtime.database.connect() as db:
        cards = json.loads(
            db.execute("SELECT body FROM game_sessions WHERE id=?", (session["id"],)).fetchone()[0]
        )["cards"]
    pairs = [[i for i, card in enumerate(cards) if card == photo] for photo in set(cards)]
    for a, b in pairs:
        session = move(client, session, a).json()
        assert session["board"]["cards"][a] == cards[a]
        session = move(client, session, b).json()
    assert session["status"] == "completed"
    assert len(session["board"]["matched"]) == 12
    assert move(client, session, 0).status_code == 409
    assert client.get("/api/state").json()["balances"][member]["available"] == 25


def test_maze_is_solvable_and_completion_ends_session(client):
    member = funded_member(client)
    session = buy(client, member)[0].json()
    grid = session["board"]["grid"]
    queue = [((1, 1), [])]
    visited = {(1, 1)}
    while queue:
        (x, y), path = queue.pop(0)
        if (x, y) == (7, 7):
            break
        for direction, (dx, dy) in {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }.items():
            target = x + dx, y + dy
            if target not in visited and not grid[target[1]][target[0]]:
                visited.add(target)
                queue.append((target, path + [direction]))
    else:
        pytest.fail("Maze has no route")
    for direction in path:
        session = move(client, session, direction).json()
    assert session["status"] == "completed"
    assert session["board"]["position"] == [7, 7]
