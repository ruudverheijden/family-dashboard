import asyncio
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import integrations, home_assistant
from .db import connect, entities, init, settings

sessions = {}
attempts = {}
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
SALT = secrets.token_bytes(16)
ADMIN_HASH = hashlib.scrypt(ADMIN_PASSWORD.encode(), salt=SALT, n=16384, r=8, p=1)

async def background():
    while True:
        await asyncio.to_thread(catch_up_background)
        await asyncio.gather(asyncio.to_thread(integrations.sync_calendars), asyncio.to_thread(integrations.sync_photos))
        await asyncio.sleep(120)

@asynccontextmanager
async def lifespan(app):
    init()
    task = asyncio.create_task(background())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title='Samen · gezinsdashboard', lifespan=lifespan, docs_url=None, redoc_url=None)

@app.middleware('http')
async def security(request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('x-family-request') != '1':
            return Response('Verzoek geweigerd', status_code=403)
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            return Response('Andere oorsprong geweigerd', status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-src http: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'"
    if request.url.path.startswith('/api'):
        response.headers['Cache-Control'] = 'no-store'
    return response

def admin(request: Request):
    key = request.cookies.get('family_admin', '')
    if sessions.get(key, 0) < time.time():
        sessions.pop(key, None)
        raise HTTPException(401, 'Meld je aan als beheerder.')

class Login(BaseModel):
    password: str = Field(max_length=500)

@app.post('/api/login')
def login(body: Login, request: Request, response: Response):
    if not ADMIN_PASSWORD or ADMIN_PASSWORD == 'vervang-dit-door-een-uniek-wachtwoord':
        raise HTTPException(503, 'Stel op de server een eigen ADMIN_PASSWORD in en herstart de app.')
    ip = request.client.host
    attempts[ip] = [t for t in attempts.get(ip, []) if t > time.time() - 300]
    if len(attempts[ip]) >= 5:
        raise HTTPException(429, 'Te veel pogingen. Probeer het over vijf minuten opnieuw.')
    candidate = hashlib.scrypt(body.password.encode(), salt=SALT, n=16384, r=8, p=1)
    if not hmac.compare_digest(candidate, ADMIN_HASH):
        attempts[ip].append(time.time())
        raise HTTPException(401, 'Het wachtwoord klopt niet.')
    attempts.pop(ip, None)
    now = time.time()
    for expired in [k for k, expiry in sessions.items() if expiry < now]:
        del sessions[expired]
    key = secrets.token_urlsafe(32)
    sessions[key] = now + 1800
    response.set_cookie('family_admin', key, httponly=True, samesite='strict', secure=os.getenv('COOKIE_SECURE', 'false') == 'true', max_age=1800)
    return {'ok': True}

@app.post('/api/logout')
def logout(request: Request, response: Response):
    sessions.pop(request.cookies.get('family_admin', ''), None)
    response.delete_cookie('family_admin')
    return {'ok': True}

def scheduled_members(kind, template, day):
    """Return the people (or one shared execution) due on a calendar day."""
    if template.get('archived') or day < template['date']:
        return []
    repeat = template.get('repeat')
    if kind == 'tasks' and repeat == 'once' and day != template['date']:
        return []
    if (kind == 'routines' or repeat == 'weekly') and date.fromisoformat(day).weekday() not in template['weekdays']:
        return []
    if kind == 'tasks' and template['mode'] == 'shared':
        return ['shared']
    return template['members']


def materialize(db, day, only_id=None):
    for kind in ('tasks', 'routines'):
        for template in entities(db, kind):
            if only_id and template['id'] != only_id:
                continue
            for person in scheduled_members(kind, template, day):
                rid = str(uuid.uuid5(uuid.NAMESPACE_URL, f'{kind}/{template["id"]}/{day}/{person}'))
                db.execute('INSERT OR IGNORE INTO runs (id,kind,template_id,day,member,body) VALUES (?,?,?,?,?,?)', (rid, kind, template['id'], day, person, json.dumps(template)))

def catch_up(db):
    today = datetime.now(ZoneInfo(settings(db)['timezone'])).date()
    for kind in ('tasks', 'routines'):
        for template in entities(db, kind):
            if template.get('archived'):
                continue
            cursor = db.execute('SELECT day FROM schedule_cursor WHERE id=?', (template['id'],)).fetchone()
            start = date.fromisoformat(cursor[0]) + timedelta(days=1) if cursor else date.fromisoformat(template['date'])
            # Bound catch-up for very old installations; never mark missed runs done.
            start = max(start, today - timedelta(days=730))
            while start <= today:
                materialize(db, start.isoformat(), template['id'])
                start += timedelta(days=1)
            db.execute('INSERT OR REPLACE INTO schedule_cursor VALUES (?,?)', (template['id'], today.isoformat()))


def catch_up_background():
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        catch_up(db)


def read_runs(db, day):
    return [{**dict(r), 'body': json.loads(r['body']), 'done': json.loads(r['done'])} for r in db.execute('SELECT * FROM runs WHERE day=? ORDER BY rowid', (day,))]

@app.get('/api/state')
def state(day: str | None = None):
    with connect() as db:
        cfg = settings(db)
        if day is None:
            day = datetime.now(ZoneInfo(cfg['timezone'])).date().isoformat()
        try:
            day = date.fromisoformat(day).isoformat()
        except ValueError:
            raise HTTPException(422, 'Ongeldige datum.')
        if abs((date.fromisoformat(day) - datetime.now(ZoneInfo(cfg['timezone'])).date()).days) > 730:
            raise HTTPException(422, 'Kies een datum binnen twee jaar van vandaag.')
        catch_up(db)
        materialize(db, day)
        return {'day': day, 'members': entities(db, 'members'), 'tasks': entities(db, 'tasks'), 'routines': entities(db, 'routines'), 'groceries': entities(db, 'groceries'), 'runs': read_runs(db, day), 'events': [e for r in db.execute('SELECT body FROM calendars') for e in json.loads(r[0])], 'status': {r['id']: json.loads(r['body']) for r in db.execute('SELECT * FROM status')}, 'config': {k: cfg[k] for k in ('timezone', 'ha_url', 'slide_seconds')}, 'photos': list(integrations.assets.values())}

class Mutation(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    id: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=0)
    action: str = 'save'
    body: dict = Field(default_factory=dict)

def text_field(data, key, maximum=200, required=False):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise HTTPException(422, f'Ongeldig veld: {key}')
    return value.strip()

def validate(kind, data, db):
    if kind == 'members':
        import re
        color = text_field(data, 'color', 7, True)
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise HTTPException(422, 'Ongeldige kleur.')
        return {'name': text_field(data, 'name', 60, True), 'color': color, 'avatar': text_field(data, 'avatar', 8)}
    if kind == 'groceries':
        if not isinstance(data.get('done', False), bool):
            raise HTTPException(422, 'Ongeldige status.')
        return {'name': text_field(data, 'name', 150, True), 'quantity': text_field(data, 'quantity', 60), 'note': text_field(data, 'note', 500), 'done': data.get('done', False)}
    title = text_field(data, 'title', 150, True)
    try:
        start_date = date.fromisoformat(data.get('date', '')).isoformat()
    except (ValueError, TypeError):
        raise HTTPException(422, 'Kies een startdatum.')
    member_ids = {x['id'] for x in entities(db, 'members')}
    people = data.get('members', [])
    if not isinstance(people, list) or not people or any(not isinstance(p, str) or p not in member_ids for p in people):
        raise HTTPException(422, 'Kies minstens één bestaand gezinslid.')
    weekdays = data.get('weekdays', list(range(7)))
    if not isinstance(weekdays, list) or not weekdays or any(type(x) is not int or x not in range(7) for x in weekdays):
        raise HTTPException(422, 'Kies geldige weekdagen.')
    if not isinstance(data.get('archived', False), bool):
        raise HTTPException(422, 'Ongeldige archiefstatus.')
    result = {'title': title, 'icon': text_field(data, 'icon', 8) or '✓', 'description': text_field(data, 'description', 1000), 'date': start_date, 'members': list(dict.fromkeys(people)), 'weekdays': weekdays, 'archived': bool(data.get('archived', False))}
    if kind == 'tasks':
        if data.get('repeat') not in ('once', 'daily', 'weekly') or data.get('mode') not in ('individual', 'shared'):
            raise HTTPException(422, 'Ongeldige herhaling of verdeling.')
        points = data.get('points', 0)
        if type(points) is not int or not 0 <= points <= 10000:
            raise HTTPException(422, 'Punten moeten tussen 0 en 10000 liggen.')
        result.update(repeat=data['repeat'], mode=data['mode'], points=points)
    else:
        steps = data.get('steps', [])
        if not isinstance(steps, list) or not 1 <= len(steps) <= 30:
            raise HTTPException(422, 'Voeg 1 tot 30 stappen toe.')
        result['steps'] = [{'text': text_field(s, 'text', 150, True), 'icon': text_field(s, 'icon', 8) or '✓'} for s in steps if isinstance(s, dict)]
        if len(result['steps']) != len(steps):
            raise HTTPException(422, 'Ongeldige stappen.')
        import re
        for field in ('start_time', 'end_time'):
            value = text_field(data, field, 5, True)
            if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', value):
                raise HTTPException(422, 'Ongeldig tijdvenster.')
            result[field] = value
        if result['end_time'] <= result['start_time']:
            raise HTTPException(422, 'Eindtijd moet na de starttijd liggen (binnen dezelfde dag).')
    return result

@app.post('/api/entities/{kind}')
def mutate(kind: str, body: Mutation, request: Request):
    if kind not in ('members', 'tasks', 'routines', 'groceries', 'runs'):
        raise HTTPException(404)
    if not _uuid(body.id):
        raise HTTPException(422, 'Ongeldig itemnummer.')
    if kind == 'members':
        admin(request)
    if body.action not in ('save', 'delete'):
        raise HTTPException(422, 'Ongeldige actie.')
    fingerprint = hashlib.sha256((kind + body.model_dump_json()).encode()).hexdigest()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT * FROM requests WHERE id=?', (body.request_id,)).fetchone()
        if previous:
            if previous['fingerprint'] != fingerprint:
                raise HTTPException(409, 'Verzoeknummer is al gebruikt.')
            return json.loads(previous['response'])
        if kind in ('tasks', 'routines'):
            catch_up(db)
        if kind == 'runs':
            row = db.execute('SELECT * FROM runs WHERE id=?', (body.id,)).fetchone()
            if not row or body.action != 'save':
                raise HTTPException(404)
            done = body.body.get('done')
            template = json.loads(row['body'])
            max_steps = len(template['steps']) if row['kind'] == 'routines' else 1
            if not isinstance(done, list) or any(type(x) is not int or not 0 <= x < max_steps for x in done):
                raise HTTPException(422, 'Ongeldige voortgang.')
            done = sorted(set(done))
            if row['version'] != body.version and done != json.loads(row['done']):
                raise HTTPException(409, 'Iemand heeft dit intussen gewijzigd. De nieuwste versie is opgehaald; controleer je wijziging.')
            version = row['version']
            if done != json.loads(row['done']):
                version += 1
                db.execute('UPDATE runs SET done=?, version=? WHERE id=?', (json.dumps(done), version, body.id))
                db.execute('INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)', ('runs', body.id, json.dumps({'before': json.loads(row['done']), 'after': done})))
        else:
            row = db.execute('SELECT * FROM entities WHERE kind=? AND id=?', (kind, body.id)).fetchone()
            version = row['version'] if row else 0
            if version != body.version:
                raise HTTPException(409, 'Iemand heeft dit intussen gewijzigd. De nieuwste versie is opgehaald; controleer je wijziging.')
            if body.action == 'delete':
                if not row:
                    raise HTTPException(404)
                if kind in ('tasks', 'routines'):
                    raise HTTPException(422, 'Archiveer het sjabloon om historie te behouden.')
                if kind == 'members':
                    used = any(body.id in x['members'] for k in ('tasks', 'routines') for x in entities(db, k))
                    used = used or db.execute('SELECT 1 FROM runs WHERE member=?', (body.id,)).fetchone() is not None
                    used = used or any(c.get('member') == body.id for a in settings(db)['caldav'] for c in a.get('calendars', []))
                    if used:
                        raise HTTPException(409, 'Dit gezinslid is gekoppeld aan taken, routines, historie of agenda’s en kan niet worden verwijderd.')
                db.execute('DELETE FROM entities WHERE kind=? AND id=?', (kind, body.id))
            else:
                data = validate(kind, body.body, db)
                db.execute('INSERT OR REPLACE INTO entities VALUES (?,?,?,?)', (kind, body.id, version + 1, json.dumps(data)))
            db.execute('INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)', (kind, body.id, json.dumps({'before': json.loads(row['body']) if row else None, 'after': body.body if body.action == 'save' else None})))
            version += 1
        result = {'ok': True, 'version': version}
        db.execute('INSERT INTO requests VALUES (?,?,?)', (body.request_id, fingerprint, json.dumps(result)))
        return result

@app.get('/api/history')
def history():
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT id,at,kind,entity_id,body FROM history ORDER BY id DESC LIMIT 100')]

@app.get('/api/admin/settings', dependencies=[Depends(admin)])
def get_settings():
    with connect() as db:
        cfg = settings(db)
    cfg['immich_configured'] = bool(cfg.pop('immich_key', ''))
    cfg['ha_configured'] = bool(cfg.pop('ha_token', ''))
    for a in cfg['caldav']:
        a['configured'] = bool(a.pop('password', ''))
    return cfg

@app.post('/api/admin/settings', dependencies=[Depends(admin)])
def save_settings(body: dict):
    with integrations.LOCK, connect() as db:
        db.execute('BEGIN IMMEDIATE')
        old = settings(db)
        if body.get('version') != old['version']:
            raise HTTPException(409, 'Instellingen zijn intussen gewijzigd. Open beheer opnieuw.')
        try:
            ZoneInfo(body.get('timezone', 'Europe/Amsterdam'))
            cfg = {k: body.get(k, old[k]) for k in ('timezone', 'ha_url', 'immich_url', 'albums', 'slide_seconds')}
            for field in ('ha_url', 'immich_url'):
                if cfg[field]:
                    cfg[field] = integrations.valid_url(cfg[field])
            if type(cfg['slide_seconds']) is not int or not 5 <= cfg['slide_seconds'] <= 300:
                raise ValueError('Wisseltijd moet tussen 5 en 300 seconden liggen.')
            cfg['immich_key'] = integrations.endpoint_secret(old['immich_url'], cfg['immich_url'], old['immich_key'], body.get('immich_key'))
            cfg['ha_token'] = body.get('ha_token') or old['ha_token']
            if body.get('ha_clear_token') is True:
                cfg['ha_token'] = ''
            if not isinstance(cfg['ha_token'], str) or len(cfg['ha_token']) > 8192 or any(c.isspace() for c in cfg['ha_token']):
                raise ValueError('Ongeldig HA-token')
            if cfg['ha_token']:
                cfg['ha_url'] = home_assistant.base_url(cfg['ha_url'])
                if cfg['ha_url'] != old['ha_url'] and old['ha_token'] and not body.get('ha_token'):
                    raise ValueError('Voer bij een ander HA-adres het token opnieuw in')
            cfg['ha_entities'] = body.get('ha_entities', old['ha_entities'])
            if not isinstance(cfg['ha_entities'], list) or len(cfg['ha_entities']) > 200 or any(not isinstance(e, str) or not home_assistant.ENTITY.fullmatch(e) for e in cfg['ha_entities']):
                raise ValueError('Ongeldige entiteiten')
            cfg['ha_entities'] = list(dict.fromkeys(cfg['ha_entities']))
            if not isinstance(cfg['albums'], list) or any(not isinstance(a, str) or not _uuid(a) for a in cfg['albums']):
                raise ValueError('Ongeldige albumselectie.')
            cfg['caldav'] = []
            seen = set()
            old_accounts = {a['id']: a for a in old['caldav']}
            for a in body.get('caldav', old['caldav']):
                aid = a.get('id') or str(uuid.uuid4())
                if aid in seen or not _uuid(aid):
                    raise ValueError('Ongeldig accountnummer.')
                seen.add(aid)
                previous = old_accounts.get(aid, {})
                account = {'id': aid, 'url': integrations.valid_url(a['url']), 'username': a['username'], 'password': integrations.endpoint_secret(previous.get('url', ''), a['url'], previous.get('password', ''), a.get('password')), 'calendars': a.get('calendars', [])}
                members = {m['id'] for m in entities(db, 'members')}
                for c in account['calendars']:
                    integrations.valid_url(c['url'])
                    if c.get('member') and c['member'] not in members:
                        raise ValueError('Onbekend gezinslid in agendakoppeling.')
                cfg['caldav'].append(account)
        except integrations.EndpointChanged as error:
            raise HTTPException(422, str(error))
        except (ValueError, KeyError, TypeError):
            raise HTTPException(422, 'Controleer adressen, tijdzone, albumselectie, wisseltijd en accounts.')
        keep = {a['id'] + ':' + c['url'] for a in cfg['caldav'] for c in a['calendars']}
        for row in db.execute('SELECT id FROM calendars').fetchall():
            if row[0] not in keep:
                db.execute('DELETE FROM calendars WHERE id=?', (row[0],))
        for row in db.execute('SELECT id FROM status').fetchall():
            if row[0].startswith('caldav:') and row[0][7:] not in seen:
                db.execute('DELETE FROM status WHERE id=?', (row[0],))
        if any(cfg[k] != old[k] for k in ('immich_url', 'immich_key', 'albums')):
            integrations.assets = {}
            integrations.purge_cache()
        db.execute('UPDATE settings SET version=version+1,body=? WHERE id=1', (json.dumps(cfg),))
    return {'ok': True}

def _uuid(value):
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False

@app.post('/api/admin/ha/discover', dependencies=[Depends(admin)])
def discover_ha(body: dict):
    with connect() as db:
        cfg = settings(db)
    url = body.get('url', cfg['ha_url'])
    token = body.get('token') or (cfg['ha_token'] if url.rstrip('/') == cfg['ha_url'].rstrip('/') else '')
    return home_assistant.discover({**cfg, 'ha_url': url, 'ha_token': token})

@app.get('/api/ha/states')
def ha_states():
    with connect() as db:
        cfg = settings(db)
    return {'configured': bool(cfg['ha_url'] and cfg['ha_token']), 'entities': home_assistant.selected_states(cfg)}

class HAControl(BaseModel):
    entity_id: str = Field(max_length=200)
    action: str = Field(max_length=30)

@app.post('/api/ha/control')
def ha_control(body: HAControl):
    with connect() as db:
        cfg = settings(db)
    return home_assistant.control(cfg, body.entity_id, body.action)

@app.post('/api/admin/discover/{service}', dependencies=[Depends(admin)])
def discover(service: str, body: dict):
    with connect() as db:
        cfg = settings(db)
    try:
        if service == 'caldav':
            previous = next((a for a in cfg['caldav'] if a['id'] == body.get('id')), {})
            account = previous | body
            account['password'] = integrations.endpoint_secret(previous.get('url', ''), account['url'], previous.get('password', ''), body.get('password'))
            integrations.valid_url(account['url'])
            return integrations.discover(account)
        if service == 'immich':
            url = integrations.valid_url(body.get('url') or cfg['immich_url'])
            cfg['immich_key'] = integrations.endpoint_secret(cfg['immich_url'], url, cfg['immich_key'], body.get('key'))
            cfg['immich_url'] = url
            return integrations.albums(cfg)
    except integrations.EndpointChanged as error:
        raise HTTPException(422, str(error))
    except Exception:
        raise HTTPException(502, 'Verbinding mislukt. Controleer serveradres, inloggegevens en rechten.')
    raise HTTPException(404)

@app.post('/api/admin/sync', dependencies=[Depends(admin)])
async def sync():
    await asyncio.gather(asyncio.to_thread(integrations.sync_calendars), asyncio.to_thread(integrations.sync_photos))
    return {'ok': True}

@app.get('/api/photos/{asset_id}')
def get_photo(asset_id: str):
    try:
        return Response(integrations.photo(asset_id), media_type='image/jpeg', headers={'Cache-Control': 'no-store'})
    except KeyError:
        raise HTTPException(404, 'Foto niet beschikbaar.')
    except Exception:
        raise HTTPException(502, 'Foto kon niet worden geladen.')

@app.get('/api/health')
def health():
    with connect() as db:
        db.execute('SELECT 1').fetchone()
    return {'status': 'ok', 'version': '0.1.0'}

STATIC = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=STATIC), name='static')
@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')
