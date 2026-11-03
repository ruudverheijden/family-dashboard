"""Atomic game purchases, versioned actions and persistent, expiring sessions."""

import hashlib
import json
import time
import uuid

from ..db import entities
from ..errors import DomainError
from ..games import GAMES, SESSION_SECONDS
from .points import point_balances


def catalog(db):
    saved = {r["id"]: dict(r) for r in db.execute("SELECT * FROM game_settings")}
    return [
        dict(
            id=key,
            title=engine.TITLE,
            description=engine.DESCRIPTION,
            icon=engine.ICON,
            price=saved.get(key, {}).get("price", 5),
            version=saved.get(key, {}).get("version", 0),
        )
        for key, engine in GAMES.items()
    ]


def configure(game_id, body, database):
    if game_id not in GAMES:
        raise DomainError(404, "Spel niet gevonden.")
    with database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = next(g for g in catalog(db) if g["id"] == game_id)
        if body.version != current["version"]:
            raise DomainError(409, "De spelprijs is inmiddels gewijzigd. Open Beheer opnieuw.")
        db.execute(
            "INSERT OR REPLACE INTO game_settings VALUES (?,?,?)",
            (game_id, body.price, body.version + 1),
        )
    return {"ok": True}


def public(row):
    result = {k: row[k] for k in ("id", "game_id", "member_id", "cost", "expires_at", "version")}
    result["status"] = (
        "expired"
        if row["status"] == "active" and row["expires_at"] <= time.time()
        else row["status"]
    )
    result["board"] = GAMES[row["game_id"]].view(json.loads(row["body"]))
    return result


def active_sessions(db):
    return [
        public(r)
        for r in db.execute(
            "SELECT * FROM game_sessions WHERE status='active' AND expires_at>?", (time.time(),)
        )
    ]


def previous_request(db, request_id, payload):
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    previous = db.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
    if previous and previous["fingerprint"] != fingerprint:
        raise DomainError(409, "Verzoeknummer is al gebruikt.")
    return fingerprint, json.loads(previous["response"]) if previous else None


def record(db, request_id, fingerprint, result):
    db.execute("INSERT INTO requests VALUES (?,?,?)", (request_id, fingerprint, json.dumps(result)))
    return result


def purchase(game_id, body, database, photos):
    if game_id not in GAMES:
        raise DomainError(404, "Spel niet gevonden.")
    # Snapshot before the transaction: preserve photo-lock/database lock order.
    available_photos = photos.snapshot() if game_id == "memory" else []
    with database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        fingerprint, previous = previous_request(
            db, body.request_id, {"kind": "game-purchase", "game": game_id, **body.model_dump()}
        )
        if previous:
            # Re-read current state: retrying a purchase never resets its board or timer.
            return public(
                db.execute("SELECT * FROM game_sessions WHERE id=?", (previous["id"],)).fetchone()
            )
        if not any(m["id"] == body.member_id for m in entities(db, "members")):
            raise DomainError(404, "Gezinslid niet gevonden.")
        if any(s["member_id"] == body.member_id for s in active_sessions(db)):
            raise DomainError(409, "Rond eerst je lopende spelsessie af.")
        game = next(g for g in catalog(db) if g["id"] == game_id)
        if body.price != game["price"] or body.version != game["version"]:
            raise DomainError(409, "De spelprijs is gewijzigd. Kies het spel opnieuw.")
        if game_id == "memory" and len(available_photos) < 6:
            raise DomainError(409, "Selecteer eerst een Immich-album met minstens 6 foto’s.")
        if point_balances(db)[body.member_id]["available"] < game["price"]:
            raise DomainError(409, "Je hebt nog niet genoeg beschikbare punten.")
        session_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO game_sessions VALUES (?,?,?,?,?,?,?,?)",
            (
                session_id,
                game_id,
                body.member_id,
                game["price"],
                time.time() + SESSION_SECONDS,
                "active",
                1,
                json.dumps(GAMES[game_id].create(available_photos)),
            ),
        )
        db.execute(
            "INSERT INTO point_transactions (id,member_id,amount,reason,source_key,related_id) VALUES (?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                body.member_id,
                -game["price"],
                "game-purchase",
                f"game:{session_id}",
                session_id,
            ),
        )
        db.execute(
            "INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)",
            (
                "games",
                session_id,
                json.dumps(
                    {"game_id": game_id, "member_id": body.member_id, "cost": game["price"]}
                ),
            ),
        )
        result = public(
            db.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        )
        return record(db, body.request_id, fingerprint, result)


def get_session(session_id, database):
    with database.connect() as db:
        row = db.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise DomainError(404, "Spelsessie niet gevonden.")
        return public(row)


def play(session_id, body, database):
    with database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        fingerprint, previous = previous_request(
            db, body.request_id, {"kind": "game-action", "session": session_id, **body.model_dump()}
        )
        if previous:
            return public(
                db.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
            )
        row = db.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise DomainError(404, "Spelsessie niet gevonden.")
        if public(row)["status"] != "active":
            raise DomainError(409, "Deze spelsessie is afgelopen.")
        if body.version != row["version"]:
            raise DomainError(409, "De spelsessie is op een ander scherm gewijzigd.")
        board = json.loads(row["body"])
        status = "stopped" if body.action == "stop" else "active"
        if body.action != "stop":
            if body.action != "move":
                raise DomainError(422, "Ongeldige spelactie.")
            try:
                if GAMES[row["game_id"]].play(board, body.value):
                    status = "completed"
            except ValueError:
                raise DomainError(422, "Deze zet is niet mogelijk.")
        db.execute(
            "UPDATE game_sessions SET body=?,status=?,version=version+1 WHERE id=?",
            (json.dumps(board), status, session_id),
        )
        result = public(
            db.execute("SELECT * FROM game_sessions WHERE id=?", (session_id,)).fetchone()
        )
        return record(db, body.request_id, fingerprint, result)
