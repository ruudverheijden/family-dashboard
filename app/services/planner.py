"""Scheduling, future routine plans and protected execution snapshots."""

import json
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from ..db import entities, settings

# A reopened execution still has history and must never become an editable plan again.
_UNSTARTED = """
    r.done='[]'
    AND NOT EXISTS (SELECT 1 FROM history h WHERE h.kind='runs' AND h.entity_id=r.id)
    AND NOT EXISTS (SELECT 1 FROM point_transactions p WHERE p.related_id=r.id)
"""


def current_day(db):
    return datetime.now(ZoneInfo(settings(db)["timezone"])).date().isoformat()


def refresh_future_routines(db):
    """Keep untouched future routine plans current, using the caller's transaction."""
    templates = {routine["id"]: routine for routine in entities(db, "routines")}
    rows = db.execute(
        f"SELECT r.* FROM runs r WHERE r.kind='routines' AND r.day>? AND {_UNSTARTED}",
        (current_day(db),),
    ).fetchall()
    for row in rows:
        template = templates.get(row["template_id"])
        if (
            template
            and row["member"] in scheduled_members("routines", template, row["day"])
            and json.loads(row["body"]) != template
        ):
            # Invalidate old open browser cards before their step indices can be applied.
            db.execute(
                "UPDATE runs SET body=?,version=version+1 WHERE id=?",
                (json.dumps(template), row["id"]),
            )


def scheduled_members(kind, template, day):
    """Return the people (or one shared execution) due on a calendar day."""
    if template.get("archived") or day < template["date"]:
        return []
    repeat = template.get("repeat")
    if kind == "tasks" and repeat == "once" and day != template["date"]:
        return []
    if (kind == "routines" or repeat == "weekly") and date.fromisoformat(
        day
    ).weekday() not in template["weekdays"]:
        return []
    if kind == "tasks" and template["mode"] == "shared":
        return ["shared"]
    return template["members"]


def materialize(db, day, only_id=None):
    for kind in ("tasks", "routines"):
        for template in entities(db, kind):
            if only_id and template["id"] != only_id:
                continue
            for person in scheduled_members(kind, template, day):
                rid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{kind}/{template['id']}/{day}/{person}"))
                db.execute(
                    "INSERT OR IGNORE INTO runs (id,kind,template_id,day,member,body) VALUES (?,?,?,?,?,?)",
                    (rid, kind, template["id"], day, person, json.dumps(template)),
                )


def catch_up(db):
    today = datetime.now(ZoneInfo(settings(db)["timezone"])).date()
    for kind in ("tasks", "routines"):
        for template in entities(db, kind):
            if template.get("archived"):
                continue
            cursor = db.execute(
                "SELECT day FROM schedule_cursor WHERE id=?", (template["id"],)
            ).fetchone()
            start = (
                date.fromisoformat(cursor[0]) + timedelta(days=1)
                if cursor
                else date.fromisoformat(template["date"])
            )
            # Bound catch-up for very old installations; never mark missed runs done.
            start = max(start, today - timedelta(days=730))
            while start <= today:
                materialize(db, start.isoformat(), template["id"])
                start += timedelta(days=1)
            db.execute(
                "INSERT OR REPLACE INTO schedule_cursor VALUES (?,?)",
                (template["id"], today.isoformat()),
            )

    refresh_future_routines(db)


def read_runs(db, start_day, end_day=None):
    end_day = end_day or start_day
    runs = [
        {**dict(r), "body": json.loads(r["body"]), "done": json.loads(r["done"])}
        for r in db.execute(
            f"""SELECT r.*, (r.kind='routines' AND r.day>? AND {_UNSTARTED}) AS follows_plan
                FROM runs r WHERE r.day BETWEEN ? AND ? ORDER BY r.day,r.rowid""",
            (current_day(db), start_day, end_day),
        )
    ]
    routine_templates = {routine["id"]: routine for routine in entities(db, "routines")}
    active_runs = []
    for run in runs:
        follows_plan = run.pop("follows_plan")
        template = routine_templates.get(run["template_id"])
        if follows_plan and (
            not template or run["member"] not in scheduled_members("routines", template, run["day"])
        ):
            continue
        active_runs.append(run)
    runs = active_runs
    task_modes = {task["id"]: task["mode"] for task in entities(db, "tasks")}
    replacements = {
        (run["template_id"], run["day"])
        for run in runs
        if run["kind"] == "tasks" and run["body"]["mode"] == task_modes.get(run["template_id"])
    }
    # A mode edit can materialize a second set of executions for the same day.
    # Hide superseded, open executions only when their replacement exists.
    # Keep snapshots, completion/undo history and the points ledger in storage.
    return [
        run
        for run in runs
        if not (
            run["kind"] == "tasks"
            and not run["done"]
            and run["body"]["mode"] != task_modes.get(run["template_id"])
            and (run["template_id"], run["day"]) in replacements
        )
    ]
