import asyncio
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import uuid
import httpx
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from . import integrations
from .db import connect, entities, init, settings

MAX_REQUEST_BODY_BYTES = 1_048_576
MAX_REQUEST_BODY_CHUNKS = 1024
LOGIN_BURST = 5
LOGIN_REFILL_SECONDS = 10


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_body_size):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for name, value in scope.get('headers', []) if name.lower() == b'content-length'),
            None,
        )
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = 0
            if declared_size > self.max_body_size:
                await self.reject(scope, receive, send)
                return

        body = bytearray()
        total_size = 0
        chunk_count = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            if message['type'] != 'http.request':
                continue
            chunk = message.get('body', b'')
            total_size += len(chunk)
            chunk_count += 1
            if total_size > self.max_body_size or chunk_count > MAX_REQUEST_BODY_CHUNKS:
                await self.reject(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get('more_body', False):
                break

        message = {'type': 'http.request', 'body': bytes(body), 'more_body': False}
        message_available = True

        async def replay_receive():
            nonlocal message_available
            if message_available:
                message_available = False
                return message
            return await receive()

        await self.app(scope, replay_receive, send)

    async def reject(self, scope, receive, send):
        response = JSONResponse(
            {'detail': 'Verzoek is te groot.'},
            status_code=413,
            headers={
                'Cache-Control': 'no-store',
                'X-Content-Type-Options': 'nosniff',
                'Referrer-Policy': 'no-referrer',
                'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; frame-src http: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'",
            },
        )
        await response(scope, receive, send)


def load_environment(env_file=None):
    load_dotenv(env_file or Path(__file__).resolve().parent.parent / '.env')

load_environment()

sessions = {}
attempts = {}
login_lock = threading.Lock()
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
app.add_middleware(RequestBodyLimitMiddleware, max_body_size=MAX_REQUEST_BODY_BYTES)

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; frame-src http: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'"
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
    ip = request.client.host if request.client else 'unknown'
    with login_lock:
        now = time.time()
        for address, timestamps in list(attempts.items()):
            active = [timestamp for timestamp in timestamps if timestamp > now - 300]
            if active:
                attempts[address] = active
            else:
                del attempts[address]
        ip_attempts = attempts.get(ip, [])
        if len(ip_attempts) >= 5:
            retry_after = max(1, int(ip_attempts[0] + 300 - now))
            raise HTTPException(
                429,
                'Te veel pogingen. Probeer het over vijf minuten opnieuw.',
                headers={'Retry-After': str(retry_after)},
            )

        retry_after = None
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            limiter = db.execute('SELECT tokens,updated_at FROM login_limiter WHERE id=1').fetchone()
            tokens = min(
                LOGIN_BURST,
                limiter['tokens'] + max(0, now - limiter['updated_at']) / LOGIN_REFILL_SECONDS,
            )
            if tokens < 1:
                retry_after = max(1, int((1 - tokens) * LOGIN_REFILL_SECONDS + 0.999))
            else:
                tokens -= 1
            db.execute(
                'UPDATE login_limiter SET tokens=?,updated_at=? WHERE id=1',
                (tokens, now),
            )
        if retry_after is not None:
            raise HTTPException(
                429,
                'Te veel aanmeldpogingen. Wacht even voordat je het opnieuw probeert.',
                headers={'Retry-After': str(retry_after)},
            )

        candidate = hashlib.scrypt(body.password.encode(), salt=SALT, n=16384, r=8, p=1)
        if not hmac.compare_digest(candidate, ADMIN_HASH):
            attempts.setdefault(ip, []).append(now)
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


def read_runs(db, start_day, end_day=None):
    end_day = end_day or start_day
    return [{**dict(r), 'body': json.loads(r['body']), 'done': json.loads(r['done'])} for r in db.execute(
        'SELECT * FROM runs WHERE day BETWEEN ? AND ? ORDER BY day,rowid', (start_day, end_day)
    )]

def point_balances(db):
    balances = {member['id']: {'balance': 0, 'reserved': 0, 'available': 0} for member in entities(db, 'members')}
    for row in db.execute('SELECT member_id, SUM(amount) AS balance FROM point_transactions GROUP BY member_id'):
        if row['member_id'] in balances:
            balances[row['member_id']]['balance'] = row['balance']
    for row in db.execute('SELECT member_id, SUM(cost) AS reserved FROM reward_requests WHERE status=? GROUP BY member_id', ('pending',)):
        if row['member_id'] in balances:
            balances[row['member_id']]['reserved'] = row['reserved']
    for balance in balances.values():
        balance['available'] = balance['balance'] - balance['reserved']
    return balances

def completion_members(run, template):
    if run['kind'] == 'tasks' and template.get('mode') == 'shared':
        return list(dict.fromkeys(template.get('members', [])))
    return [run['member']]

def completion_award(run, done):
    template = json.loads(run['body'])
    if run['kind'] == 'tasks':
        complete = 0 in done
    else:
        complete = len(done) == len(template.get('steps', []))
    return (template, complete, template.get('points', 0))

def update_completion_points(db, run, done, completion_version):
    template, complete, points = completion_award(run, done)
    if run['kind'] not in ('tasks', 'routines') or not points:
        return
    members = completion_members(run, template)
    if complete:
        for member_id in members:
            db.execute(
                'INSERT OR IGNORE INTO point_transactions (id,member_id,amount,reason,source_key,related_id) VALUES (?,?,?,?,?,?)',
                (str(uuid.uuid4()), member_id, points, 'completion', f'run:{run["id"]}:completion:{completion_version}:{member_id}', run['id']),
            )
        return
    originals = db.execute(
        '''SELECT award.* FROM point_transactions award
           LEFT JOIN point_transactions reversal ON reversal.reverses_id=award.id
           WHERE award.related_id=? AND award.reason='completion' AND reversal.id IS NULL''',
        (run['id'],),
    ).fetchall()
    for award in originals:
        db.execute(
            'INSERT OR IGNORE INTO point_transactions (id,member_id,amount,reason,source_key,related_id,reverses_id) VALUES (?,?,?,?,?,?,?)',
            (str(uuid.uuid4()), award['member_id'], -award['amount'], 'completion-undone', f'reversal:{award["id"]}', run['id'], award['id']),
        )

@app.get('/api/state')
def state(day: str | None = None, period: str = 'day'):
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
        if period not in ('day', 'three-day', 'week'):
            raise HTTPException(422, 'Ongeldige agenda-periode.')
        selected_day = date.fromisoformat(day)
        start_day = selected_day - timedelta(days=selected_day.weekday()) if period == 'week' else selected_day
        if period == 'week':
            end_day = start_day + timedelta(days=6)
        elif period == 'three-day':
            end_day = start_day + timedelta(days=2)
        else:
            end_day = start_day
        catch_up(db)
        current_day = start_day
        while current_day <= end_day:
            materialize(db, current_day.isoformat())
            current_day += timedelta(days=1)
        statuses = {r['id']: json.loads(r['body']) for r in db.execute('SELECT * FROM status')}
        for account in cfg['caldav']:
            key = 'caldav:' + account['id']
            status = statuses.setdefault(key, {'ok': False, 'message': 'Nog niet bijgewerkt', 'last_success': None})
            status['calendars'] = [
                {'name': selection.get('name') or 'Agenda'}
                for selection in account.get('calendars', [])
            ]
        return {
            'day': day,
            'members': entities(db, 'members'),
            'tasks': entities(db, 'tasks'),
            'routines': entities(db, 'routines'),
            'groceries': entities(db, 'groceries'),
            'runs': read_runs(db, start_day.isoformat(), end_day.isoformat()),
            'events': [e for r in db.execute('SELECT body FROM calendars') for e in json.loads(r[0])],
            'status': statuses,
            'config': {k: cfg[k] for k in ('timezone', 'ha_url', 'ha_dashboard', 'slide_seconds')} | {
                'caldav_configured': bool(cfg['caldav']),
            },
            'photos': list(integrations.assets.values()),
            'rewards': [reward for reward in entities(db, 'rewards') if not reward.get('archived')],
            'balances': point_balances(db),
            'reward_requests': [dict(row) for row in db.execute(
                'SELECT * FROM reward_requests ORDER BY CASE status WHEN ? THEN 0 ELSE 1 END, created_at DESC LIMIT 100',
                ('pending',),
            )],
            'point_transactions': [dict(row) for row in db.execute(
                'SELECT * FROM point_transactions ORDER BY created_at DESC, rowid DESC LIMIT 100'
            )],
        }

class Mutation(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    id: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=0)
    action: str = 'save'
    body: dict = Field(default_factory=dict)

class RewardRequestInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    member_id: str
    reward_id: str

class RewardDecisionInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    action: str

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
    if kind == 'rewards':
        price = data.get('price')
        if type(price) is not int or not 1 <= price <= 100000:
            raise HTTPException(422, 'De puntenprijs moet tussen 1 en 100000 liggen.')
        return {
            'title': text_field(data, 'title', 100, True),
            'description': text_field(data, 'description', 500),
            'icon': text_field(data, 'icon', 8) or '🎁',
            'price': price,
        }
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
    points = data.get('points', 0)
    if type(points) is not int or not 0 <= points <= 10000:
        raise HTTPException(422, 'Punten moeten tussen 0 en 10000 liggen.')
    result['points'] = points
    if kind == 'tasks':
        if data.get('repeat') not in ('once', 'daily', 'weekly') or data.get('mode') not in ('individual', 'shared'):
            raise HTTPException(422, 'Ongeldige herhaling of verdeling.')
        result.update(repeat=data['repeat'], mode=data['mode'])
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
    if kind not in ('members', 'tasks', 'routines', 'groceries', 'rewards', 'runs'):
        raise HTTPException(404)
    if not _uuid(body.id):
        raise HTTPException(422, 'Ongeldig itemnummer.')
    if kind in ('members', 'rewards'):
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
                update_completion_points(db, row, done, version)
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
                    used = used or db.execute('SELECT 1 FROM point_transactions WHERE member_id=?', (body.id,)).fetchone() is not None
                    used = used or db.execute('SELECT 1 FROM reward_requests WHERE member_id=?', (body.id,)).fetchone() is not None
                    if used:
                        raise HTTPException(409, 'Dit gezinslid is gekoppeld aan taken, routines, historie of agenda’s en kan niet worden verwijderd.')
                if kind == 'rewards' and db.execute(
                    'SELECT 1 FROM reward_requests WHERE reward_id=? AND status=?', (body.id, 'pending')
                ).fetchone():
                    raise HTTPException(409, 'Deze beloning heeft nog openstaande aanvragen en kan niet worden verwijderd.')
                db.execute('DELETE FROM entities WHERE kind=? AND id=?', (kind, body.id))
            else:
                data = validate(kind, body.body, db)
                db.execute('INSERT OR REPLACE INTO entities VALUES (?,?,?,?)', (kind, body.id, version + 1, json.dumps(data)))
            db.execute('INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)', (kind, body.id, json.dumps({'before': json.loads(row['body']) if row else None, 'after': body.body if body.action == 'save' else None})))
            version += 1
        result = {'ok': True, 'version': version}
        db.execute('INSERT INTO requests VALUES (?,?,?)', (body.request_id, fingerprint, json.dumps(result)))
        return result

@app.post('/api/reward-requests')
def request_reward(body: RewardRequestInput):
    if not _uuid(body.member_id) or not _uuid(body.reward_id):
        raise HTTPException(422, 'Ongeldig gezinslid of beloningsnummer.')
    fingerprint = hashlib.sha256(json.dumps(
        {'kind': 'reward-request', **body.model_dump()}, sort_keys=True
    ).encode()).hexdigest()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT * FROM requests WHERE id=?', (body.request_id,)).fetchone()
        if previous:
            if previous['fingerprint'] != fingerprint:
                raise HTTPException(409, 'Verzoeknummer is al gebruikt.')
            return json.loads(previous['response'])
        member = next((item for item in entities(db, 'members') if item['id'] == body.member_id), None)
        reward = next((item for item in entities(db, 'rewards') if item['id'] == body.reward_id), None)
        if not member or not reward or reward.get('archived'):
            raise HTTPException(404, 'Gezinslid of beloning niet gevonden.')
        balance = point_balances(db)[body.member_id]
        if balance['available'] < reward['price']:
            raise HTTPException(409, 'Er zijn niet genoeg beschikbare punten voor deze beloning.')
        request_id = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO reward_requests
               (id,member_id,member_name,reward_id,reward_name,cost,status)
               VALUES (?,?,?,?,?,?,?)''',
            (request_id, body.member_id, member['name'], body.reward_id, reward['title'], reward['price'], 'pending'),
        )
        db.execute(
            'INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)',
            ('reward-requests', request_id, json.dumps({
                'member_id': body.member_id, 'member_name': member['name'],
                'reward_id': body.reward_id, 'reward_name': reward['title'],
                'cost': reward['price'], 'status': 'pending',
            })),
        )
        result = {'ok': True, 'id': request_id, 'status': 'pending'}
        db.execute('INSERT INTO requests VALUES (?,?,?)', (body.request_id, fingerprint, json.dumps(result)))
        return result

@app.post('/api/admin/reward-requests/{reward_request_id}/decision', dependencies=[Depends(admin)])
def decide_reward_request(reward_request_id: str, body: RewardDecisionInput):
    if not _uuid(reward_request_id):
        raise HTTPException(422, 'Ongeldig aanvraagnummer.')
    if body.action not in ('approve', 'reject'):
        raise HTTPException(422, 'Kies goedkeuren of afwijzen.')
    fingerprint = hashlib.sha256(json.dumps({
        'kind': 'reward-decision', 'id': reward_request_id, **body.model_dump(),
    }, sort_keys=True).encode()).hexdigest()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT * FROM requests WHERE id=?', (body.request_id,)).fetchone()
        if previous:
            if previous['fingerprint'] != fingerprint:
                raise HTTPException(409, 'Verzoeknummer is al gebruikt.')
            return json.loads(previous['response'])
        reward_request = db.execute(
            'SELECT * FROM reward_requests WHERE id=?', (reward_request_id,)
        ).fetchone()
        if not reward_request:
            raise HTTPException(404, 'Beloningsaanvraag niet gevonden.')
        if reward_request['status'] != 'pending':
            raise HTTPException(409, 'Deze beloningsaanvraag is al afgehandeld.')
        if body.action == 'approve':
            balance = db.execute(
                'SELECT COALESCE(SUM(amount),0) FROM point_transactions WHERE member_id=?',
                (reward_request['member_id'],),
            ).fetchone()[0]
            reserved_other = db.execute(
                'SELECT COALESCE(SUM(cost),0) FROM reward_requests WHERE member_id=? AND status=? AND id!=?',
                (reward_request['member_id'], 'pending', reward_request_id),
            ).fetchone()[0]
            if balance - reserved_other < reward_request['cost']:
                raise HTTPException(409, 'Het saldo is niet meer toereikend om deze aanvraag goed te keuren.')
            db.execute(
                '''INSERT INTO point_transactions
                   (id,member_id,amount,reason,source_key,related_id)
                   VALUES (?,?,?,?,?,?)''',
                (
                    str(uuid.uuid4()), reward_request['member_id'], -reward_request['cost'],
                    'reward-redemption', f'reward-request:{reward_request_id}:redemption', reward_request_id,
                ),
            )
        status = 'approved' if body.action == 'approve' else 'rejected'
        db.execute(
            'UPDATE reward_requests SET status=?,resolved_at=CURRENT_TIMESTAMP WHERE id=?',
            (status, reward_request_id),
        )
        db.execute(
            'INSERT INTO history(kind,entity_id,body) VALUES (?,?,?)',
            ('reward-requests', reward_request_id, json.dumps({
                'member_id': reward_request['member_id'], 'member_name': reward_request['member_name'],
                'reward_id': reward_request['reward_id'], 'reward_name': reward_request['reward_name'],
                'cost': reward_request['cost'], 'status': status,
            })),
        )
        result = {'ok': True, 'id': reward_request_id, 'status': status}
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
            cfg = {k: body.get(k, old[k]) for k in ('timezone', 'ha_url', 'ha_dashboard', 'immich_url', 'albums', 'slide_seconds')}
            if cfg['ha_url']:
                cfg['ha_url'] = integrations.valid_url(cfg['ha_url'])
                parsed = urlsplit(cfg['ha_url'])
                if parsed.path not in ('', '/') or parsed.query or '?' in cfg['ha_url'] or '#' in cfg['ha_url']:
                    raise ValueError('Gebruik het Home Assistant-basisadres zonder dashboardpad.')
                _ = parsed.port
            if not isinstance(cfg['ha_dashboard'], str) or len(cfg['ha_dashboard']) > 500 or not re.fullmatch(r'/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/?', cfg['ha_dashboard']):
                raise ValueError('Ongeldig Home Assistant-dashboardpad.')
            if cfg['immich_url']:
                cfg['immich_url'] = integrations.valid_url(cfg['immich_url'])
            if type(cfg['slide_seconds']) is not int or not 5 <= cfg['slide_seconds'] <= 300:
                raise ValueError('Wisseltijd moet tussen 5 en 300 seconden liggen.')
            cfg['immich_key'] = integrations.endpoint_secret(old['immich_url'], cfg['immich_url'], old['immich_key'], body.get('immich_key'))
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
    except httpx.HTTPStatusError as error:
        if error.response.status_code in (401, 403):
            raise HTTPException(403, 'Immich weigert toegang tot de foto. Geef de API-sleutel in Immich het recht asset.view en vernieuw daarna deze pagina.')
        raise HTTPException(502, 'Foto kon niet worden geladen.')
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
