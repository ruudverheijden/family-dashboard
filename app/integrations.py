"""Read-only adapters. Never expose credentials or upstream exception bodies."""
import hashlib
import json
import os
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import caldav
import httpx
from icalendar import Calendar
import recurring_ical_events
from .db import connect, settings

LOCK = threading.RLock()
CACHE = Path(os.getenv('CACHE_DIR', './cache'))
CACHE_LIMIT = int(os.getenv('CACHE_MB', '128')) * 1024 * 1024
assets = {}

def valid_url(value):
    p = urlparse(value)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError('Gebruik een http(s)-adres zonder inloggegevens of fragment.')
    return value.rstrip('/')

class EndpointChanged(ValueError):
    """Stored credentials must not follow a changed endpoint."""


def endpoint_secret(old_url, new_url, saved, supplied):
    if supplied:
        return supplied
    if saved and old_url.rstrip('/') != new_url.rstrip('/'):
        if not new_url:
            return ''
        raise EndpointChanged('Voer bij een ander serveradres het geheim opnieuw in.')
    return saved


def client(account):
    return caldav.DAVClient(url=account['url'], username=account['username'], password=account['password'], timeout=20)

def discover(account):
    with client(account) as c:
        return [{'url': str(x.url), 'name': str(x.name or 'Agenda')} for x in c.principal().calendars()]

def expand_ics(raw, start, end, tz):
    result = []
    for event in recurring_ical_events.of(Calendar.from_ical(raw)).between(start, end):
        if str(event.get('STATUS', '')) == 'CANCELLED':
            continue
        dt = event.decoded('DTSTART')
        finish = event.decoded('DTEND', dt)
        all_day = not isinstance(dt, datetime)
        def iso(value):
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=tz)
                return value.astimezone(tz).isoformat()
            return value.isoformat()
        result.append({'id': str(event.get('UID')) + ':' + iso(dt), 'title': str(event.get('SUMMARY', 'Afspraak')), 'start': iso(dt), 'end': iso(finish), 'all_day': all_day, 'location': str(event.get('LOCATION', ''))})
    return result

def set_status(db, key, ok, message):
    row = db.execute('SELECT body FROM status WHERE id=?', (key,)).fetchone()
    old = json.loads(row[0]) if row else {}
    body = {'ok': ok, 'message': message, 'last_success': datetime.now(timezone.utc).isoformat() if ok else old.get('last_success')}
    db.execute('INSERT OR REPLACE INTO status VALUES (?,?)', (key, json.dumps(body)))

def sync_calendars():
    with LOCK:
        with connect() as db:
            cfg = settings(db)
        tz = ZoneInfo(cfg['timezone'])
        today = datetime.now(tz).date()
        start = datetime.combine(today - timedelta(days=90), datetime.min.time(), tzinfo=tz)
        end = start + timedelta(days=456)
        for account in cfg['caldav']:
            key = 'caldav:' + account['id']
            try:
                records = []
                with client(account) as c:
                    available = {str(x.url): x for x in c.principal().calendars()}
                    for selection in account.get('calendars', []):
                        cal = available[selection['url']]
                        events = {}
                        for resource in cal.search(start=start, end=end, event=True, expand=False):
                            for event in expand_ics(resource.data, start, end, tz):
                                event.update(member=selection.get('member', ''), calendar=selection.get('name', 'Agenda'))
                                events[event['id']] = event
                        records.append((account['id'] + ':' + selection['url'], list(events.values())))
                with connect() as db:
                    for cid, events in records:
                        db.execute('INSERT OR REPLACE INTO calendars VALUES (?,?)', (cid, json.dumps(events)))
                    set_status(db, key, True, 'Bijgewerkt')
            except Exception:
                with connect() as db:
                    set_status(db, key, False, 'Synchronisatie mislukt. Controleer adres, account en geselecteerde agenda’s. Laatste gegevens blijven bewaard.')

def immich_get(cfg, path):
    return httpx.get(cfg['immich_url'].rstrip('/') + '/api' + path, headers={'x-api-key': cfg['immich_key']}, timeout=20, follow_redirects=False)

def albums(cfg):
    response = immich_get(cfg, '/albums')
    response.raise_for_status()
    return [{'id': a['id'], 'name': a['albumName']} for a in response.json()]

def sync_photos():
    global assets
    with LOCK:
        with connect() as db:
            cfg = settings(db)
        if not cfg['immich_url'] or not cfg['albums']:
            assets = {}
            purge_cache()
            return
        try:
            fresh = {}
            for album in cfg['albums']:
                r = immich_get(cfg, '/albums/' + album)
                r.raise_for_status()
                for asset in r.json().get('assets', []):
                    if asset.get('type') == 'IMAGE' and not asset.get('isTrashed', False):
                        fresh[asset['id']] = {'id': asset['id'], 'album': r.json().get('albumName', 'Album')}
            assets = fresh
            purge_cache()
            with connect() as db:
                set_status(db, 'immich', True, 'Albums bijgewerkt')
        except Exception:
            # Fail closed: cannot establish whether cached images are still allowed.
            assets = {}
            purge_cache()
            with connect() as db:
                set_status(db, 'immich', False, 'Immich niet bereikbaar of album niet toegankelijk. Controleer de verbinding en API-sleutel.')

def purge_cache():
    CACHE.mkdir(parents=True, exist_ok=True)
    allowed = {hashlib.sha256(x.encode()).hexdigest() for x in assets}
    for path in CACHE.iterdir():
        if path.is_file() and path.name not in allowed:
            path.unlink(missing_ok=True)
    files = sorted((p for p in CACHE.iterdir() if p.is_file()), key=lambda p: p.stat().st_mtime)
    total = sum(p.stat().st_size for p in files)
    for p in files:
        if total <= CACHE_LIMIT:
            break
        total -= p.stat().st_size
        p.unlink(missing_ok=True)

def photo(asset_id):
    with LOCK:
        if asset_id not in assets:
            raise KeyError(asset_id)
        CACHE.mkdir(parents=True, exist_ok=True)
        path = CACHE / hashlib.sha256(asset_id.encode()).hexdigest()
        if path.exists():
            os.utime(path, None)
            return path.read_bytes()
        with connect() as db:
            cfg = settings(db)
        r = immich_get(cfg, '/assets/' + asset_id + '/thumbnail?size=preview')
        r.raise_for_status()
        if not r.headers.get('content-type', '').startswith('image/') or len(r.content) > min(CACHE_LIMIT, 20 * 1024 * 1024):
            raise ValueError('Ongeldige afbeelding')
        path.write_bytes(r.content)
        purge_cache()
        return r.content
