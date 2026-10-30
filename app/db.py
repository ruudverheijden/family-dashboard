import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATA = Path(os.getenv('DATA_DIR', './data'))

@contextmanager
def connect():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(DATA / 'family.db', timeout=15)
    (DATA / 'family.db').chmod(0o600)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

def init():
    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version > 2:
            raise RuntimeError('Database is nieuwer dan deze applicatie')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS entities (kind TEXT, id TEXT, version INTEGER NOT NULL, body TEXT NOT NULL, PRIMARY KEY(kind,id));
        CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, kind TEXT, template_id TEXT, day TEXT, member TEXT, body TEXT, done TEXT NOT NULL DEFAULT '[]', version INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS schedule_cursor (id TEXT PRIMARY KEY, day TEXT);
        CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, at TEXT DEFAULT CURRENT_TIMESTAMP, kind TEXT, entity_id TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, fingerprint TEXT, response TEXT);
        CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS calendars (id TEXT PRIMARY KEY, body TEXT);
        CREATE TABLE IF NOT EXISTS status (id TEXT PRIMARY KEY, body TEXT);
        CREATE TABLE IF NOT EXISTS point_transactions (
            id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK(amount != 0),
            reason TEXT NOT NULL,
            source_key TEXT NOT NULL UNIQUE,
            related_id TEXT NOT NULL,
            reverses_id TEXT UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reward_requests (
            id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            member_name TEXT NOT NULL,
            reward_id TEXT NOT NULL,
            reward_name TEXT NOT NULL,
            cost INTEGER NOT NULL CHECK(cost > 0),
            status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT
        );
        CREATE INDEX IF NOT EXISTS reward_requests_status ON reward_requests(status, created_at);
        PRAGMA user_version=2;
        ''')
        db.execute('INSERT OR IGNORE INTO settings VALUES (1,1,?)', (json.dumps({'timezone': 'Europe/Amsterdam', 'caldav': [], 'ha_url': '', 'ha_dashboard': '/lovelace/0', 'immich_url': '', 'immich_key': '', 'albums': [], 'slide_seconds': 15}),))
        row = db.execute('SELECT body FROM settings WHERE id=1').fetchone()
        stored = json.loads(row['body'])
        legacy_token = stored.pop('ha_token', None)
        legacy_entities = stored.pop('ha_entities', None)
        if legacy_token is not None or legacy_entities is not None:
            db.execute('UPDATE settings SET body=? WHERE id=1', (json.dumps(stored),))

def settings(db):
    row = db.execute('SELECT * FROM settings WHERE id=1').fetchone()
    stored = json.loads(row['body'])
    stored.pop('ha_token', None)
    stored.pop('ha_entities', None)
    return {'ha_dashboard': '/lovelace/0', **stored, 'version': row['version']}

def entities(db, kind):
    return [{**json.loads(r['body']), 'id': r['id'], 'version': r['version']} for r in db.execute('SELECT * FROM entities WHERE kind=? ORDER BY rowid', (kind,))]
