"""Point ledger operations."""

import hashlib
import json
import uuid

from ..db import entities
from ..errors import DomainError
from ..validation import _uuid


def point_balances(db):
    balances = {
        member["id"]: {"balance": 0, "reserved": 0, "available": 0}
        for member in entities(db, "members")
    }
    for row in db.execute(
        "SELECT member_id, SUM(amount) AS balance FROM point_transactions GROUP BY member_id"
    ):
        if row["member_id"] in balances:
            balances[row["member_id"]]["balance"] = row["balance"]
    for row in db.execute(
        "SELECT member_id, SUM(cost) AS reserved FROM reward_requests WHERE status=? GROUP BY member_id",
        ("pending",),
    ):
        if row["member_id"] in balances:
            balances[row["member_id"]]["reserved"] = row["reserved"]
    for balance in balances.values():
        balance["available"] = balance["balance"] - balance["reserved"]
    return balances


def adjust_points(body, database):
    if not _uuid(body.member_id):
        raise DomainError(422, "Ongeldig gezinslid.")
    reason = body.reason.strip()
    if body.amount == 0:
        raise DomainError(422, "De correctie mag niet nul punten zijn.")

    payload = body.model_dump() | {"reason": reason}
    fingerprint = hashlib.sha256(
        json.dumps({"kind": "points-adjustment", **payload}, sort_keys=True).encode()
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
        if not member:
            raise DomainError(404, "Gezinslid niet gevonden.")

        balance = point_balances(db)[body.member_id]
        if balance["available"] + body.amount < 0:
            raise DomainError(
                409,
                "De correctie kan niet lager zijn dan de voor beloningen gereserveerde punten.",
            )

        transaction_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO point_transactions
               (id,member_id,amount,reason,source_key,related_id)
               VALUES (?,?,?,?,?,?)""",
            (
                transaction_id,
                body.member_id,
                body.amount,
                f"manual-adjustment:{reason}" if reason else "manual-adjustment",
                f"points-adjustment:{body.request_id}",
                body.member_id,
            ),
        )
        result = {
            "ok": True,
            "id": transaction_id,
            "balance": balance["balance"] + body.amount,
            "available": balance["available"] + body.amount,
        }
        db.execute(
            "INSERT INTO requests VALUES (?,?,?)",
            (body.request_id, fingerprint, json.dumps(result)),
        )
        return result


def completion_members(run, template):
    if run["kind"] == "tasks" and template.get("mode") == "shared":
        return list(dict.fromkeys(template.get("members", [])))
    return [run["member"]]


def completion_award(run, done):
    template = json.loads(run["body"])
    if run["kind"] == "tasks":
        complete = 0 in done
    else:
        complete = len(done) == len(template.get("steps", []))
    return (template, complete, template.get("points", 0))


def update_completion_points(db, run, done, completion_version):
    template, complete, points = completion_award(run, done)
    if run["kind"] not in ("tasks", "routines") or not points:
        return
    members = completion_members(run, template)
    if complete:
        for member_id in members:
            db.execute(
                "INSERT OR IGNORE INTO point_transactions (id,member_id,amount,reason,source_key,related_id) VALUES (?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    member_id,
                    points,
                    "completion",
                    f"run:{run['id']}:completion:{completion_version}:{member_id}",
                    run["id"],
                ),
            )
        return
    originals = db.execute(
        """SELECT award.* FROM point_transactions award
           LEFT JOIN point_transactions reversal ON reversal.reverses_id=award.id
           WHERE award.related_id=? AND award.reason='completion' AND reversal.id IS NULL""",
        (run["id"],),
    ).fetchall()
    for award in originals:
        db.execute(
            "INSERT OR IGNORE INTO point_transactions (id,member_id,amount,reason,source_key,related_id,reverses_id) VALUES (?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                award["member_id"],
                -award["amount"],
                "completion-undone",
                f"reversal:{award['id']}",
                run["id"],
                award["id"],
            ),
        )
