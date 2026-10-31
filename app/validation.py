"""Entity normalization and validation. No HTTP or application startup dependencies."""

import base64
import binascii
import re
import uuid
from datetime import date

from .db import entities
from .errors import DomainError


def text_field(data, key, maximum=200, required=False):
    value = data.get(key, "")
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise DomainError(422, f"Ongeldig veld: {key}")
    return value.strip()


def member_avatar(value):
    if not isinstance(value, str):
        raise DomainError(422, "Upload een geldige profielfoto.")
    if value == "":
        return ""
    if len(value) <= 8 and not value.startswith("data:"):
        return value.strip()
    if len(value) > 220_000:
        raise DomainError(422, "De profielfoto is ongeldig of te groot.")
    match = re.fullmatch(r"data:image/jpeg;base64,([A-Za-z0-9+/]*={0,2})", value)
    if not match:
        raise DomainError(422, "Upload een geldige JPEG-profielfoto.")
    try:
        image = base64.b64decode(match.group(1), validate=True)
    except (ValueError, binascii.Error):
        raise DomainError(422, "Upload een geldige JPEG-profielfoto.")
    if len(image) > 160_000 or not image.startswith(b"\xff\xd8\xff"):
        raise DomainError(422, "De profielfoto is ongeldig of te groot.")
    return value


def validate(kind, data, db):
    if kind == "members":
        role = data.get("role", "child")
        if role not in ("child", "parent"):
            raise DomainError(422, "Kies of dit gezinslid een kind of ouder is.")
        color = text_field(data, "color", 7, True)
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise DomainError(422, "Ongeldige kleur.")
        return {
            "name": text_field(data, "name", 60, True),
            "color": color,
            "avatar": member_avatar(data.get("avatar", "")),
            "role": role,
        }
    if kind == "groceries":
        if not isinstance(data.get("done", False), bool):
            raise DomainError(422, "Ongeldige status.")
        return {
            "name": text_field(data, "name", 150, True),
            "quantity": text_field(data, "quantity", 60),
            "note": text_field(data, "note", 500),
            "done": data.get("done", False),
        }
    if kind == "rewards":
        price = data.get("price")
        if type(price) is not int or not 1 <= price <= 100000:
            raise DomainError(422, "De puntenprijs moet tussen 1 en 100000 liggen.")
        return {
            "title": text_field(data, "title", 100, True),
            "description": text_field(data, "description", 500),
            "icon": text_field(data, "icon", 8) or "🎁",
            "price": price,
        }
    title = text_field(data, "title", 150, True)
    try:
        start_date = date.fromisoformat(data.get("date", "")).isoformat()
    except (ValueError, TypeError):
        raise DomainError(422, "Kies een startdatum.")
    member_ids = {x["id"] for x in entities(db, "members")}
    people = data.get("members", [])
    if (
        not isinstance(people, list)
        or not people
        or any(not isinstance(p, str) or p not in member_ids for p in people)
    ):
        raise DomainError(422, "Kies minstens één bestaand gezinslid.")
    weekdays = data.get("weekdays", list(range(7)))
    if (
        not isinstance(weekdays, list)
        or not weekdays
        or any(type(x) is not int or x not in range(7) for x in weekdays)
    ):
        raise DomainError(422, "Kies geldige weekdagen.")
    if not isinstance(data.get("archived", False), bool):
        raise DomainError(422, "Ongeldige archiefstatus.")
    result = {
        "title": title,
        "icon": text_field(data, "icon", 8) or "✓",
        "description": text_field(data, "description", 1000),
        "date": start_date,
        "members": list(dict.fromkeys(people)),
        "weekdays": weekdays,
        "archived": bool(data.get("archived", False)),
    }
    points = data.get("points", 0)
    if type(points) is not int or not 0 <= points <= 10000:
        raise DomainError(422, "Punten moeten tussen 0 en 10000 liggen.")
    result["points"] = points
    if kind == "tasks":
        if data.get("repeat") not in ("once", "daily", "weekly") or data.get("mode") not in (
            "individual",
            "shared",
        ):
            raise DomainError(422, "Ongeldige herhaling of verdeling.")
        result.update(repeat=data["repeat"], mode=data["mode"])
    else:
        steps = data.get("steps", [])
        if not isinstance(steps, list) or not 1 <= len(steps) <= 30:
            raise DomainError(422, "Voeg 1 tot 30 stappen toe.")
        result["steps"] = [
            {"text": text_field(s, "text", 150, True), "icon": text_field(s, "icon", 8) or "✓"}
            for s in steps
            if isinstance(s, dict)
        ]
        if len(result["steps"]) != len(steps):
            raise DomainError(422, "Ongeldige stappen.")
        for field in ("start_time", "end_time"):
            value = text_field(data, field, 5, True)
            if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", value):
                raise DomainError(422, "Ongeldig tijdvenster.")
            result[field] = value
        if result["end_time"] <= result["start_time"]:
            raise DomainError(422, "Eindtijd moet na de starttijd liggen (binnen dezelfde dag).")
    return result


def _uuid(value):
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False
