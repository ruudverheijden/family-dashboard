"""Read-only CalDAV adapter. Network work never holds a settings or photo lock."""

import json
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import caldav
import recurring_ical_events
from icalendar import Calendar

from ..db import settings
from .common import log_failure, set_status

CALENDAR_SYNC_INTERVAL = 180


def client(account):
    return caldav.DAVClient(
        url=account["url"], username=account["username"], password=account["password"], timeout=20
    )


def discover(account):
    with client(account) as c:
        return [
            {"url": str(x.url), "name": str(x.name or "Agenda")} for x in c.principal().calendars()
        ]


def expand_ics(raw, start, end, tz):
    result = []
    for event in recurring_ical_events.of(Calendar.from_ical(raw)).between(start, end):
        if str(event.get("STATUS", "")) == "CANCELLED":
            continue
        dt = event.decoded("DTSTART")
        finish = event.decoded("DTEND", dt)
        all_day = not isinstance(dt, datetime)

        def iso(value):
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=tz)
                return value.astimezone(tz).isoformat()
            return value.isoformat()

        result.append(
            {
                "id": str(event.get("UID")) + ":" + iso(dt),
                "title": str(event.get("SUMMARY", "Afspraak")),
                "start": iso(dt),
                "end": iso(finish),
                "all_day": all_day,
                "location": str(event.get("LOCATION", "")),
            }
        )
    return result


class CalendarSync:
    def __init__(self, database):
        self.database = database
        self.guard = threading.Lock()
        self.last_sync = None

    def sync(self):
        with self.guard:
            now = time.monotonic()
            if self.last_sync is not None and now - self.last_sync < CALENDAR_SYNC_INTERVAL:
                return
            self.last_sync = now
            self.fetch_and_publish()

    def fetch_and_publish(self):
        with self.database.connect() as db:
            cfg = settings(db)
        tz = ZoneInfo(cfg["timezone"])
        today = datetime.now(tz).date()
        start = datetime.combine(today - timedelta(days=90), datetime.min.time(), tzinfo=tz)
        end = start + timedelta(days=456)
        for account in cfg["caldav"]:
            key = "caldav:" + account["id"]
            try:
                records = []
                with client(account) as c:
                    available = {str(x.url): x for x in c.principal().calendars()}
                    for selection in account.get("calendars", []):
                        cal = available[selection["url"]]
                        events = {}
                        for resource in cal.search(start=start, end=end, event=True, expand=False):
                            for event in expand_ics(resource.data, start, end, tz):
                                event.update(
                                    member=selection.get("member", ""),
                                    calendar=selection.get("name", "Agenda"),
                                )
                                events[event["id"]] = event
                        records.append(
                            (account["id"] + ":" + selection["url"], list(events.values()))
                        )
                with self.database.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    if settings(db)["version"] != cfg["version"]:
                        continue
                    for cid, events in records:
                        db.execute(
                            "INSERT OR REPLACE INTO calendars VALUES (?,?)",
                            (cid, json.dumps(events)),
                        )
                    set_status(db, key, True, "Bijgewerkt")
            except Exception as error:
                log_failure("CalDAV synchronization", error)
                with self.database.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    if settings(db)["version"] == cfg["version"]:
                        set_status(
                            db,
                            key,
                            False,
                            "Synchronisatie mislukt. Controleer adres, account en geselecteerde agenda’s. Laatste gegevens blijven bewaard.",
                        )
