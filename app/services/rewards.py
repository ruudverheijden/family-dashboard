"""Reward reservations and decisions, including idempotency and ledger writes."""

import hashlib
import json
import uuid

from ..db import entities
from ..errors import DomainError
from ..schemas import RewardDecisionInput, RewardRequestInput
from ..validation import _uuid
from .points import point_balances


def request_reward(body: RewardRequestInput, database):
    if not _uuid(body.member_id) or not _uuid(body.reward_id):
        raise DomainError(422, "Ongeldig gezinslid of beloningsnummer.")
    fingerprint = hashlib.sha256(
        json.dumps({"kind": "reward-request", **body.model_dump()}, sort_keys=True).encode()
    ).hexdigest()
    with database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT * FROM requests WHERE id=?", (body.request_id,)).fetchone()
        if previous:
            if previous["fingerprint"] != fingerprint:
                raise DomainError(409, "Verzoeknummer is al gebruikt.")
            return json.loads(previous["response"])
        member = next(
            (item for item in entities(db, "members") if item["id"] == body.member_id), None
        )
        reward = next(
            (item for item in entities(db, "rewards") if item["id"] == body.reward_id), None
        )
        if not member or not reward or reward.get("archived"):
            raise DomainError(404, "Gezinslid of beloning niet gevonden.")
        balance = point_balances(db)[body.member_id]
        if balance["available"] < reward["price"]:
            raise DomainError(409, "Er zijn niet genoeg beschikbare punten voor deze beloning.")
        request_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO reward_requests
               (id,member_id,member_name,reward_id,reward_name,cost,status)
               VALUES (?,?,?,?,?,?,?)""",
            (
                request_id,
                body.member_id,
                member["name"],
                body.reward_id,
                reward["title"],
                reward["price"],
                "pending",
            ),
        )
        db.execute(
            "INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)",
            (
                "reward-requests",
                request_id,
                json.dumps(
                    {
                        "member_id": body.member_id,
                        "member_name": member["name"],
                        "reward_id": body.reward_id,
                        "reward_name": reward["title"],
                        "cost": reward["price"],
                        "status": "pending",
                    }
                ),
            ),
        )
        result = {"ok": True, "id": request_id, "status": "pending"}
        db.execute(
            "INSERT INTO requests VALUES (?,?,?)",
            (body.request_id, fingerprint, json.dumps(result)),
        )
        return result


def decide_reward_request(reward_request_id: str, body: RewardDecisionInput, database):
    if not _uuid(reward_request_id):
        raise DomainError(422, "Ongeldig aanvraagnummer.")
    if body.action not in ("approve", "reject"):
        raise DomainError(422, "Kies goedkeuren of afwijzen.")
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "kind": "reward-decision",
                "id": reward_request_id,
                **body.model_dump(),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    with database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT * FROM requests WHERE id=?", (body.request_id,)).fetchone()
        if previous:
            if previous["fingerprint"] != fingerprint:
                raise DomainError(409, "Verzoeknummer is al gebruikt.")
            return json.loads(previous["response"])
        reward_request = db.execute(
            "SELECT * FROM reward_requests WHERE id=?", (reward_request_id,)
        ).fetchone()
        if not reward_request:
            raise DomainError(404, "Beloningsaanvraag niet gevonden.")
        if reward_request["status"] != "pending":
            raise DomainError(409, "Deze beloningsaanvraag is al afgehandeld.")
        if body.action == "approve":
            balance = db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM point_transactions WHERE member_id=?",
                (reward_request["member_id"],),
            ).fetchone()[0]
            reserved_other = db.execute(
                "SELECT COALESCE(SUM(cost),0) FROM reward_requests WHERE member_id=? AND status=? AND id!=?",
                (reward_request["member_id"], "pending", reward_request_id),
            ).fetchone()[0]
            if balance - reserved_other < reward_request["cost"]:
                raise DomainError(
                    409, "Het saldo is niet meer toereikend om deze aanvraag goed te keuren."
                )
            db.execute(
                """INSERT INTO point_transactions
                   (id,member_id,amount,reason,source_key,related_id)
                   VALUES (?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    reward_request["member_id"],
                    -reward_request["cost"],
                    "reward-redemption",
                    f"reward-request:{reward_request_id}:redemption",
                    reward_request_id,
                ),
            )
        status = "approved" if body.action == "approve" else "rejected"
        db.execute(
            "UPDATE reward_requests SET status=?,resolved_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, reward_request_id),
        )
        db.execute(
            "INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)",
            (
                "reward-requests",
                reward_request_id,
                json.dumps(
                    {
                        "member_id": reward_request["member_id"],
                        "member_name": reward_request["member_name"],
                        "reward_id": reward_request["reward_id"],
                        "reward_name": reward_request["reward_name"],
                        "cost": reward_request["cost"],
                        "status": status,
                    }
                ),
            ),
        )
        result = {"ok": True, "id": reward_request_id, "status": status}
        db.execute(
            "INSERT INTO requests VALUES (?,?,?)",
            (body.request_id, fingerprint, json.dumps(result)),
        )
        return result
