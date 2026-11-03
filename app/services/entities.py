"""Versioned entity writes, execution completion and history in one transaction."""

import hashlib
import json

from ..db import entities, settings
from ..errors import DomainError
from ..schemas import Mutation
from ..validation import _uuid, validate
from .planner import catch_up, read_runs, refresh_future_routines
from .points import update_completion_points


def history_snapshot(value):
    snapshot = dict(value) if value else value
    if snapshot is None:
        return None
    snapshot.pop("avatar_changed", None)
    avatar = snapshot.get("avatar", "")
    if isinstance(avatar, str) and avatar.startswith("data:image/jpeg;base64,"):
        snapshot["avatar"] = ""
        snapshot["has_photo"] = True
    return snapshot


def mutate(kind: str, body: Mutation, database):
    if kind not in ("members", "tasks", "routines", "groceries", "rewards", "runs"):
        raise DomainError(404)
    if not _uuid(body.id):
        raise DomainError(422, "Ongeldig itemnummer.")
    if body.action not in ("save", "delete"):
        raise DomainError(422, "Ongeldige actie.")
    fingerprint = hashlib.sha256((kind + body.model_dump_json()).encode()).hexdigest()
    with database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT * FROM requests WHERE id=?", (body.request_id,)).fetchone()
        if previous:
            if previous["fingerprint"] != fingerprint:
                raise DomainError(409, "Verzoeknummer is al gebruikt.")
            return json.loads(previous["response"])
        if kind in ("tasks", "routines"):
            catch_up(db)
        if kind == "runs":
            row = db.execute("SELECT * FROM runs WHERE id=?", (body.id,)).fetchone()
            if not row or body.action != "save":
                raise DomainError(404)
            if row["kind"] == "routines":
                refresh_future_routines(db)
                row = db.execute("SELECT * FROM runs WHERE id=?", (body.id,)).fetchone()
                if not any(run["id"] == body.id for run in read_runs(db, row["day"])):
                    raise DomainError(
                        409, "De routineplanning is gewijzigd. Vernieuw het overzicht."
                    )
            done = body.body.get("done")
            template = json.loads(row["body"])
            max_steps = len(template["steps"]) if row["kind"] == "routines" else 1
            if not isinstance(done, list) or any(
                type(x) is not int or not 0 <= x < max_steps for x in done
            ):
                raise DomainError(422, "Ongeldige voortgang.")
            done = sorted(set(done))
            if row["version"] != body.version and done != json.loads(row["done"]):
                raise DomainError(
                    409,
                    "Iemand heeft dit intussen gewijzigd. De nieuwste versie is opgehaald; controleer je wijziging.",
                )
            version = row["version"]
            if done != json.loads(row["done"]):
                version += 1
                db.execute(
                    "UPDATE runs SET done=?, version=? WHERE id=?",
                    (json.dumps(done), version, body.id),
                )
                update_completion_points(db, row, done, version)
                db.execute(
                    "INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)",
                    (
                        "runs",
                        body.id,
                        json.dumps({"before": json.loads(row["done"]), "after": done}),
                    ),
                )
        else:
            row = db.execute(
                "SELECT * FROM entities WHERE kind=? AND id=?", (kind, body.id)
            ).fetchone()
            version = row["version"] if row else 0
            if version != body.version:
                raise DomainError(
                    409,
                    "Iemand heeft dit intussen gewijzigd. De nieuwste versie is opgehaald; controleer je wijziging.",
                )
            if body.action == "delete":
                if not row:
                    raise DomainError(404)
                if kind in ("tasks", "routines"):
                    raise DomainError(422, "Archiveer het sjabloon om historie te behouden.")
                if kind == "members":
                    used = any(
                        body.id in x["members"]
                        for k in ("tasks", "routines")
                        for x in entities(db, k)
                    )
                    used = (
                        used
                        or db.execute("SELECT 1 FROM runs WHERE member=?", (body.id,)).fetchone()
                        is not None
                    )
                    used = used or any(
                        c.get("member") == body.id
                        for a in settings(db)["caldav"]
                        for c in a.get("calendars", [])
                    )
                    used = (
                        used
                        or db.execute(
                            "SELECT 1 FROM point_transactions WHERE member_id=?", (body.id,)
                        ).fetchone()
                        is not None
                    )
                    used = (
                        used
                        or db.execute(
                            "SELECT 1 FROM reward_requests WHERE member_id=?", (body.id,)
                        ).fetchone()
                        is not None
                    )
                    if used:
                        raise DomainError(
                            409,
                            "Dit gezinslid is gekoppeld aan taken, routines, historie of agenda’s en kan niet worden verwijderd.",
                        )
                if (
                    kind == "rewards"
                    and db.execute(
                        "SELECT 1 FROM reward_requests WHERE reward_id=? AND status=?",
                        (body.id, "pending"),
                    ).fetchone()
                ):
                    raise DomainError(
                        409,
                        "Deze beloning heeft nog openstaande aanvragen en kan niet worden verwijderd.",
                    )
                db.execute("DELETE FROM entities WHERE kind=? AND id=?", (kind, body.id))
            else:
                incoming = dict(body.body)
                if kind == "members":
                    avatar_changed = str(incoming.pop("avatar_changed", "")).lower() in (
                        "true",
                        "1",
                    )
                    if not avatar_changed and not incoming.get("avatar") and row:
                        incoming["avatar"] = json.loads(row["body"]).get("avatar", "")
                data = validate(kind, incoming, db)
                db.execute(
                    "INSERT OR REPLACE INTO entities VALUES (?,?,?,?)",
                    (kind, body.id, version + 1, json.dumps(data)),
                )
            db.execute(
                "INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)",
                (
                    kind,
                    body.id,
                    json.dumps(
                        {
                            "before": history_snapshot(json.loads(row["body"])) if row else None,
                            "after": (history_snapshot(data) if kind != "runs" else body.body)
                            if body.action == "save"
                            else None,
                        }
                    ),
                ),
            )
            version += 1
            if kind == "routines":
                refresh_future_routines(db)
        result = {"ok": True, "version": version}
        db.execute(
            "INSERT INTO requests VALUES (?,?,?)",
            (body.request_id, fingerprint, json.dumps(result)),
        )
        return result
