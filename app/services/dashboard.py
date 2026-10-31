"""Dashboard query, including the existing on-demand execution materialization contract."""

import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from ..db import entities, settings
from ..errors import DomainError
from .planner import catch_up, materialize, read_runs
from .points import point_balances


def state(database, photos, day: str | None = None, period: str = "day"):
    with database.connect() as db:
        cfg = settings(db)
        if day is None:
            day = datetime.now(ZoneInfo(cfg["timezone"])).date().isoformat()
        try:
            day = date.fromisoformat(day).isoformat()
        except ValueError:
            raise DomainError(422, "Ongeldige datum.")
        if (
            abs((date.fromisoformat(day) - datetime.now(ZoneInfo(cfg["timezone"])).date()).days)
            > 730
        ):
            raise DomainError(422, "Kies een datum binnen twee jaar van vandaag.")
        if period not in ("day", "three-day", "week"):
            raise DomainError(422, "Ongeldige agenda-periode.")
        selected_day = date.fromisoformat(day)
        start_day = (
            selected_day - timedelta(days=selected_day.weekday())
            if period == "week"
            else selected_day
        )
        if period == "week":
            end_day = start_day + timedelta(days=6)
        elif period == "three-day":
            end_day = start_day + timedelta(days=2)
        else:
            end_day = start_day
        catch_up(db)
        current_day = start_day
        while current_day <= end_day:
            materialize(db, current_day.isoformat())
            current_day += timedelta(days=1)
        statuses = {r["id"]: json.loads(r["body"]) for r in db.execute("SELECT * FROM status")}
        for account in cfg["caldav"]:
            key = "caldav:" + account["id"]
            status = statuses.setdefault(
                key, {"ok": False, "message": "Nog niet bijgewerkt", "last_success": None}
            )
            status["calendars"] = [
                {"name": selection.get("name") or "Agenda"}
                for selection in account.get("calendars", [])
            ]
        result = {
            "day": day,
            "members": entities(db, "members"),
            "tasks": entities(db, "tasks"),
            "routines": entities(db, "routines"),
            "groceries": entities(db, "groceries"),
            "runs": read_runs(db, start_day.isoformat(), end_day.isoformat()),
            "events": [
                e for r in db.execute("SELECT body FROM calendars") for e in json.loads(r[0])
            ],
            "status": statuses,
            "config": {
                k: cfg[k]
                for k in (
                    "timezone",
                    "ha_url",
                    "ha_dashboard",
                    "slide_seconds",
                    "brand_title",
                    "brand_subtitle",
                )
            }
            | {
                "brand_image": bool(cfg["brand_image"]),
                "brand_version": cfg["version"],
                "caldav_configured": bool(cfg["caldav"]),
            },
            "rewards": [reward for reward in entities(db, "rewards") if not reward.get("archived")],
            "balances": point_balances(db),
            "reward_requests": [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM reward_requests ORDER BY CASE status WHEN ? THEN 0 ELSE 1 END, created_at DESC LIMIT 100",
                    ("pending",),
                )
            ],
            "point_transactions": [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM point_transactions ORDER BY created_at DESC, rowid DESC LIMIT 100"
                )
            ],
        }

    # Release the database transaction before acquiring the photo lock.
    result["photos"] = photos.snapshot()
    return result


def history(database):
    with database.connect() as db:
        return [
            dict(r)
            for r in db.execute(
                "SELECT id,at,kind,entity_id,body FROM history ORDER BY id DESC LIMIT 100"
            )
        ]
