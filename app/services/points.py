"""Point ledger. Call within the execution mutation transaction."""

import json
import uuid

from ..db import entities


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
