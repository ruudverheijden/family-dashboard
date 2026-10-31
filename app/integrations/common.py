"""Shared endpoint policy and sanitized integration status."""

import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse


def valid_url(value):
    p = urlparse(value)
    if (
        p.scheme not in ("http", "https")
        or not p.hostname
        or p.username
        or p.password
        or p.fragment
    ):
        raise ValueError("Gebruik een http(s)-adres zonder inloggegevens of fragment.")
    return value.rstrip("/")


class EndpointChanged(ValueError):
    """Stored credentials must not follow a changed endpoint."""


def endpoint_secret(old_url, new_url, saved, supplied):
    if supplied:
        return supplied
    if saved and old_url.rstrip("/") != new_url.rstrip("/"):
        if not new_url:
            return ""
        raise EndpointChanged("Voer bij een ander serveradres het geheim opnieuw in.")
    return saved


def set_status(db, key, ok, message):
    row = db.execute("SELECT body FROM status WHERE id=?", (key,)).fetchone()
    old = json.loads(row[0]) if row else {}
    body = {
        "ok": ok,
        "message": message,
        "last_success": datetime.now(timezone.utc).isoformat() if ok else old.get("last_success"),
    }
    db.execute("INSERT OR REPLACE INTO status VALUES (?,?)", (key, json.dumps(body)))


def log_failure(service, error):
    # Exception messages/tracebacks can contain URLs, credentials or upstream bodies.
    logging.getLogger(__name__).warning("%s failed (%s)", service, type(error).__name__)
