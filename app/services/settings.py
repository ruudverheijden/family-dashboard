"""Validated settings updates and invalidation of obsolete integration results."""

import base64
import binascii
import json
import re
import uuid
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from ..db import entities, settings
from ..errors import DomainError
from ..integrations import common as integrations
from ..validation import _uuid, text_field


def get_settings(database):
    with database.connect() as db:
        cfg = settings(db)
    cfg["immich_configured"] = bool(cfg.pop("immich_key", ""))
    for a in cfg["caldav"]:
        a["configured"] = bool(a.pop("password", ""))
    return cfg


def save_settings(body: dict, database, photos):
    with photos.lock, database.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        old = settings(db)
        if body.get("version") != old["version"]:
            raise DomainError(409, "Instellingen zijn intussen gewijzigd. Open beheer opnieuw.")
        try:
            ZoneInfo(body.get("timezone", "Europe/Amsterdam"))
            cfg = {
                k: body.get(k, old[k])
                for k in (
                    "timezone",
                    "ha_url",
                    "ha_dashboard",
                    "immich_url",
                    "albums",
                    "slide_seconds",
                )
            }
            cfg.update(
                {
                    "brand_title": text_field(
                        {"brand_title": body.get("brand_title", old["brand_title"])},
                        "brand_title",
                        40,
                        True,
                    ),
                    "brand_subtitle": text_field(
                        {"brand_subtitle": body.get("brand_subtitle", old["brand_subtitle"])},
                        "brand_subtitle",
                        80,
                    ),
                    "brand_image": validate_brand_image(
                        body.get("brand_image", old["brand_image"])
                    ),
                }
            )
            if cfg["ha_url"]:
                cfg["ha_url"] = integrations.valid_url(cfg["ha_url"])
                parsed = urlsplit(cfg["ha_url"])
                if (
                    parsed.path not in ("", "/")
                    or parsed.query
                    or "?" in cfg["ha_url"]
                    or "#" in cfg["ha_url"]
                ):
                    raise ValueError("Gebruik het Home Assistant-basisadres zonder dashboardpad.")
                _ = parsed.port
            if (
                not isinstance(cfg["ha_dashboard"], str)
                or len(cfg["ha_dashboard"]) > 500
                or not re.fullmatch(r"/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/?", cfg["ha_dashboard"])
            ):
                raise ValueError("Ongeldig Home Assistant-dashboardpad.")
            if cfg["immich_url"]:
                cfg["immich_url"] = integrations.valid_url(cfg["immich_url"])
            if type(cfg["slide_seconds"]) is not int or not 5 <= cfg["slide_seconds"] <= 300:
                raise ValueError("Wisseltijd moet tussen 5 en 300 seconden liggen.")
            cfg["immich_key"] = integrations.endpoint_secret(
                old["immich_url"], cfg["immich_url"], old["immich_key"], body.get("immich_key")
            )
            if not isinstance(cfg["albums"], list) or any(
                not isinstance(a, str) or not _uuid(a) for a in cfg["albums"]
            ):
                raise ValueError("Ongeldige albumselectie.")
            cfg["caldav"] = []
            seen = set()
            old_accounts = {a["id"]: a for a in old["caldav"]}
            for a in body.get("caldav", old["caldav"]):
                aid = a.get("id") or str(uuid.uuid4())
                if aid in seen or not _uuid(aid):
                    raise ValueError("Ongeldig accountnummer.")
                seen.add(aid)
                previous = old_accounts.get(aid, {})
                account = {
                    "id": aid,
                    "url": integrations.valid_url(a["url"]),
                    "username": a["username"],
                    "password": integrations.endpoint_secret(
                        previous.get("url", ""),
                        a["url"],
                        previous.get("password", ""),
                        a.get("password"),
                    ),
                    "calendars": a.get("calendars", []),
                }
                members = {m["id"] for m in entities(db, "members")}
                for c in account["calendars"]:
                    integrations.valid_url(c["url"])
                    if c.get("member") and c["member"] not in members:
                        raise ValueError("Onbekend gezinslid in agendakoppeling.")
                cfg["caldav"].append(account)
        except integrations.EndpointChanged as error:
            raise DomainError(422, str(error))
        except (ValueError, KeyError, TypeError):
            raise DomainError(
                422, "Controleer adressen, tijdzone, albumselectie, wisseltijd en accounts."
            )
        keep = {a["id"] + ":" + c["url"] for a in cfg["caldav"] for c in a["calendars"]}
        for row in db.execute("SELECT id FROM calendars").fetchall():
            if row[0] not in keep:
                db.execute("DELETE FROM calendars WHERE id=?", (row[0],))
        for row in db.execute("SELECT id FROM status").fetchall():
            if row[0].startswith("caldav:") and row[0][7:] not in seen:
                db.execute("DELETE FROM status WHERE id=?", (row[0],))
        if any(cfg[k] != old[k] for k in ("immich_url", "immich_key", "albums")):
            photos.invalidate()
        db.execute("UPDATE settings SET version=version+1,body=? WHERE id=1", (json.dumps(cfg),))
    return {"ok": True}


def validate_brand_image(value):
    if value == "":
        return ""
    if not isinstance(value, str) or len(value) > 540_000:
        raise DomainError(422, "De gezinsfoto is ongeldig of te groot.")
    match = re.fullmatch(r"data:image/jpeg;base64,([A-Za-z0-9+/]*={0,2})", value)
    if not match:
        raise DomainError(422, "Upload een geldige JPEG-afbeelding.")
    try:
        image = base64.b64decode(match.group(1), validate=True)
    except (ValueError, binascii.Error):
        raise DomainError(422, "Upload een geldige JPEG-afbeelding.")
    if len(image) > 400_000 or not image.startswith(b"\xff\xd8\xff"):
        raise DomainError(422, "De gezinsfoto is ongeldig of te groot.")
    return value
