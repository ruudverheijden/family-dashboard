import json
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from app import db, integrations, main

HEAD = {'X-Family-Request': '1'}
SYNC_CALENDARS = integrations.sync_calendars
SYNC_PHOTOS = integrations.sync_photos

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DATA', tmp_path / 'data')
    monkeypatch.setattr(integrations, 'CACHE', tmp_path / 'cache')
    monkeypatch.setattr(integrations, 'assets', {})
    monkeypatch.setattr(integrations, 'sync_calendars', lambda: None)
    monkeypatch.setattr(integrations, 'sync_photos', lambda: None)
    main.sessions.clear()
    main.sessions['test-admin'] = 10**12
    with TestClient(main.app, headers=HEAD) as c:
        c.cookies.set('family_admin', 'test-admin')
        yield c

def create(c, kind, body, id=None, version=0, request_id=None, action='save'):
    id = id or str(uuid.uuid4())
    result = c.post('/api/entities/' + kind, json={'request_id': request_id or str(uuid.uuid4()), 'id': id, 'version': version, 'body': body, 'action': action})
    return id, result

def setup_task(c, mode='individual', kind='tasks', members=1):
    people = [create(c, 'members', {'name': f'Persoon {i}', 'color': '#aa7755'})[0] for i in range(members)]
    today = c.get('/api/state').json()['day']
    body = {'title': 'Testtaak', 'icon': '✓', 'date': today, 'repeat': 'daily', 'mode': mode, 'members': people, 'weekdays': list(range(7)), 'points': 5}
    if kind == 'routines':
        body.update(steps=[{'text': 'Stap één', 'icon': '✓'}, {'text': 'Stap twee', 'icon': '☀'}], start_time='07:00', end_time='09:00')
    id, result = create(c, kind, body)
    assert result.status_code == 200, result.text
    return id, body, today

def test_admin_and_secret_isolation(client):
    cfg = client.get('/api/admin/settings').json()
    cfg.update(immich_url='http://immich.example.org', immich_key='TOPSECRET')
    assert client.post('/api/admin/settings', json=cfg).status_code == 200
    assert 'TOPSECRET' not in client.get('/api/state').text
    assert 'TOPSECRET' not in client.get('/api/admin/settings').text
    client.cookies.clear()
    assert client.get('/api/admin/settings').status_code == 401
    assert create(client, 'members', {'name':'No', 'color':'#ffffff'})[1].status_code == 401
    assert client.post('/api/admin/sync').status_code == 401

def test_cross_origin_rejected(client):
    assert client.post('/api/logout', headers={'Origin':'https://evil.example'}).status_code == 403
    with TestClient(main.app) as c:
        assert c.post('/api/logout').status_code == 403

def test_groceries_idempotency_conflict_and_restore(client):
    rid = str(uuid.uuid4())
    id, r = create(client, 'groceries', {'name':'Appels'}, request_id=rid)
    assert r.status_code == 200
    assert create(client, 'groceries', {'name':'Appels'}, id=id, request_id=rid)[1].status_code == 200
    assert len(client.get('/api/state').json()['groceries']) == 1
    assert create(client, 'groceries', {'name':'Peren'}, id=id, request_id=rid)[1].status_code == 409
    assert create(client, 'groceries', {'name':'Appels', 'done':True}, id=id, version=1)[1].status_code == 200
    assert create(client, 'groceries', {'name':'Anders'}, id=id, version=1)[1].status_code == 409
    assert create(client, 'groceries', {'name':'Appels', 'done':False}, id=id, version=2)[1].status_code == 200
    assert client.get('/api/state').json()['groceries'][0]['done'] is False

def test_simultaneous_task_completion_one_history_entry(client):
    setup_task(client, mode='shared', members=2)
    run = client.get('/api/state').json()['runs'][0]
    def complete(_):
        return create(client,'runs',{'done':[0]},id=run['id'],version=1)[1].status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(complete, range(2))) == [200,200]
    runs = client.get('/api/state').json()['runs']
    assert len(runs) == 1 and runs[0]['done'] == [0] and runs[0]['version'] == 2
    history = client.get('/api/history').json()
    assert len([h for h in history if h['kind']=='runs']) == 1

def test_individual_tasks_and_routine_new_day(client):
    setup_task(client, members=2)
    _, _, today = setup_task(client, kind='routines', members=2)
    runs = client.get('/api/state').json()['runs']
    assert len(runs) == 4
    run = next(r for r in runs if r['kind']=='routines')
    assert create(client,'runs',{'done':[0]},id=run['id'],version=1)[1].status_code == 200
    assert next(r for r in client.get('/api/state').json()['runs'] if r['id']==run['id'])['done'] == [0]
    tomorrow = (datetime.fromisoformat(today)+timedelta(days=1)).date().isoformat()
    assert all(r['done'] == [] for r in client.get('/api/state',params={'day':tomorrow}).json()['runs'])
    assert next(r for r in client.get('/api/state').json()['runs'] if r['id']==run['id'])['done'] == [0]

def test_routine_concurrent_different_steps_conflict(client):
    setup_task(client,kind='routines')
    run = client.get('/api/state').json()['runs'][0]
    assert create(client,'runs',{'done':[0]},id=run['id'],version=1)[1].status_code == 200
    assert create(client,'runs',{'done':[1]},id=run['id'],version=1)[1].status_code == 409
    assert create(client,'runs',{'done':[0,1]},id=run['id'],version=2)[1].status_code == 200

def test_template_edits_preserve_snapshot(client):
    id, body, today = setup_task(client)
    old = client.get('/api/state').json()['runs'][0]
    assert create(client,'tasks',{**body,'title':'Nieuwe titel'},id=id,version=1)[1].status_code==200
    assert client.get('/api/state').json()['runs'][0]['body']['title'] == old['body']['title']
    assert create(client,'tasks',{**body,'archived':True},id=id,version=2)[1].status_code==200
    tomorrow = (datetime.fromisoformat(today)+timedelta(days=1)).date().isoformat()
    assert not client.get('/api/state',params={'day':tomorrow}).json()['runs']

def test_sqlite_backup_restore(client, tmp_path, monkeypatch):
    create(client,'groceries',{'name':'Brood','quantity':'2 stuks'})
    cfg=client.get('/api/admin/settings').json()
    cfg['immich_key']='backup-secret'
    client.post('/api/admin/settings',json=cfg)
    restored=tmp_path/'restored'
    restored.mkdir()
    with sqlite3.connect(db.DATA/'family.db') as source, sqlite3.connect(restored/'family.db') as dest:
        source.backup(dest)
    monkeypatch.setattr(db,'DATA',restored)
    db.init()
    assert client.get('/api/state').json()['groceries'][0]['name']=='Brood'
    with db.connect() as c:
        assert db.settings(c)['immich_key']=='backup-secret'

def test_future_schema_refused(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DATA',tmp_path)
    with sqlite3.connect(tmp_path/'family.db') as c:
        c.execute('PRAGMA user_version=999')
    with pytest.raises(RuntimeError): db.init()

def test_unselected_photo_never_requested(client, monkeypatch):
    monkeypatch.setattr(integrations,'immich_get',lambda *a:pytest.fail('Must not request arbitrary photos'))
    assert client.get('/api/photos/unknown').status_code==404

def test_ical_dst_exception_all_day():
    raw='''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//NL
BEGIN:VEVENT
UID:recurrence
DTSTART;TZID=Europe/Amsterdam:20261024T090000
DTEND;TZID=Europe/Amsterdam:20261024T100000
RRULE:FREQ=DAILY;COUNT=3
EXDATE;TZID=Europe/Amsterdam:20261025T090000
SUMMARY:Origineel
END:VEVENT
BEGIN:VEVENT
UID:recurrence
RECURRENCE-ID;TZID=Europe/Amsterdam:20261026T090000
DTSTART;TZID=Europe/Amsterdam:20261026T110000
DTEND;TZID=Europe/Amsterdam:20261026T120000
SUMMARY:Verplaatst
END:VEVENT
BEGIN:VEVENT
UID:all-day
DTSTART;VALUE=DATE:20261025
DTEND;VALUE=DATE:20261027
SUMMARY:Hele dag
END:VEVENT
END:VCALENDAR'''
    tz=ZoneInfo('Europe/Amsterdam')
    events=integrations.expand_ics(raw,datetime(2026,10,23,tzinfo=tz),datetime(2026,10,28,tzinfo=tz),tz)
    assert len(events)==3
    assert next(e for e in events if e['title']=='Origineel')['start']=='2026-10-24T09:00:00+02:00'
    assert next(e for e in events if e['title']=='Verplaatst')['start']=='2026-10-26T11:00:00+01:00'
    assert next(e for e in events if e['title']=='Hele dag')['all_day'] is True

def test_missed_days_materialized_before_template_edit(client):
    id, body, today = setup_task(client)
    earlier=(datetime.fromisoformat(today)-timedelta(days=2)).date().isoformat()
    # Simulate a template saved before a server was offline for two days.
    with db.connect() as c:
        stored={**body,'date':earlier}
        c.execute('UPDATE entities SET body=? WHERE id=?',(json.dumps(stored),id))
        c.execute('DELETE FROM schedule_cursor WHERE id=?',(id,))
    assert create(client,'tasks',{**stored,'title':'Updated'},id=id,version=1)[1].status_code==200
    with db.connect() as c:
        runs=c.execute('SELECT * FROM runs WHERE template_id=?',(id,)).fetchall()
        assert len(runs)==3
        assert all(json.loads(r['body'])['title']=='Testtaak' and json.loads(r['done'])==[] for r in runs)

def test_caldav_atomic_replacement_and_failure_keeps_cache(client, monkeypatch):
    # Use the real sync function despite the fixture disabling background network work.
    from types import SimpleNamespace
    real = integrations
    monkeypatch.setattr(real,'CACHE',db.DATA.parent/'cache')
    account={'id':str(uuid.uuid4()),'url':'http://calendar.example.org','username':'test','password':'secret','calendars':[{'url':'http://calendar.example.org/a/','name':'Gezin','member':''}]}
    with db.connect() as c:
        cfg=db.settings(c)
        cfg['caldav']=[account]
        c.execute('UPDATE settings SET body=?',(json.dumps(cfg),))
    raw='BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nUID:demo\nDTSTART:20261030T090000Z\nDTEND:20261030T100000Z\nSUMMARY:Afspraak\nEND:VEVENT\nEND:VCALENDAR'
    resources=[SimpleNamespace(data=raw)]
    class Fake:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def principal(self): return self
        def calendars(self): return [self]
        url='http://calendar.example.org/a/'
        def search(self,**kwargs): return resources
    monkeypatch.setattr(real,'client',lambda a:Fake())
    SYNC_CALENDARS()
    assert len(client.get('/api/state').json()['events'])==1
    resources[:]=[SimpleNamespace(data=raw.replace('Afspraak','Gewijzigd'))]
    SYNC_CALENDARS()
    assert client.get('/api/state').json()['events'][0]['title']=='Gewijzigd'
    monkeypatch.setattr(real,'client',lambda a:(_ for _ in ()).throw(OSError('private server data')))
    SYNC_CALENDARS()
    state=client.get('/api/state').json()
    assert len(state['events'])==1 and state['status']['caldav:'+account['id']]['ok'] is False
    assert 'private server data' not in json.dumps(state)
    monkeypatch.setattr(real,'client',lambda a:Fake())
    resources.clear()
    SYNC_CALENDARS()
    assert client.get('/api/state').json()['events']==[]

def test_immich_album_revocation_and_bounded_cache(client, monkeypatch):
    import httpx
    aid=str(uuid.uuid4());pid=str(uuid.uuid4())
    with db.connect() as c:
        cfg=db.settings(c)
        cfg.update(immich_url='http://immich.example.org',immich_key='secret',albums=[aid])
        c.execute('UPDATE settings SET body=?',(json.dumps(cfg),))
    response={'albumName':'Testalbum','assets':[{'id':pid,'type':'IMAGE'}]}
    def fake_get(cfg,path):
        return httpx.Response(200,json=response,request=httpx.Request('GET','http://immich.example.org'))
    monkeypatch.setattr(integrations,'immich_get',fake_get)
    real_sync=SYNC_PHOTOS
    monkeypatch.setattr(integrations,'CACHE',db.DATA.parent/'cache')
    monkeypatch.setattr(integrations,'immich_get',fake_get)
    real_sync()
    assert pid in integrations.assets
    import hashlib
    path=integrations.CACHE/hashlib.sha256(pid.encode()).hexdigest()
    path.write_bytes(b'test-cache')
    response['assets']=[]
    real_sync()
    assert pid not in integrations.assets and not path.exists()
    assert client.get('/api/photos/'+pid).status_code==404
    monkeypatch.setattr(integrations,'CACHE_LIMIT',5)
    integrations.assets={'a':{},'b':{}}
    for id in ('a','b'):
        (integrations.CACHE/hashlib.sha256(id.encode()).hexdigest()).write_bytes(b'1234')
    integrations.purge_cache()
    assert sum(p.stat().st_size for p in integrations.CACHE.iterdir())<=5

def test_untrusted_entity_ids_rejected(client):
    assert create(client,'groceries',{'name':'Test'},id='\"><img src=x>')[1].status_code==422

def configure_ha(client):
    cfg=client.get('/api/admin/settings').json()
    cfg.update(ha_url='http://ha.example.org:8123',ha_token='secret-ha-token',ha_entities=['light.kitchen','sensor.temperature'])
    assert client.post('/api/admin/settings',json=cfg).status_code==200
    return cfg

def test_ha_token_private_preserved_and_revoked(client):
    configure_ha(client)
    cfg=client.get('/api/admin/settings').json()
    assert cfg['ha_configured'] and 'ha_token' not in cfg
    assert 'secret-ha-token' not in client.get('/api/state').text
    assert client.post('/api/admin/settings',json=cfg).status_code==200
    with db.connect() as c: assert db.settings(c)['ha_token']=='secret-ha-token'
    cfg=client.get('/api/admin/settings').json()
    cfg.update(ha_clear_token=True)
    assert client.post('/api/admin/settings',json=cfg).status_code==200
    assert not client.get('/api/admin/settings').json()['ha_configured']

def test_ha_bearer_and_entity_allowlist(client,monkeypatch):
    from app import home_assistant as ha
    import httpx
    configure_ha(client)
    calls=[]
    class FakeClient:
        def __init__(self,**kwargs): assert kwargs['follow_redirects'] is False
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def request(self,method,url,headers,json):
            assert headers['Authorization']=='Bearer secret-ha-token'
            calls.append((method,url,json))
            payload=[{'entity_id':'light.kitchen','state':'on','attributes':{'friendly_name':'Keuken'}},{'entity_id':'sensor.temperature','state':'20','attributes':{'unit_of_measurement':'°C'}},{'entity_id':'lock.frontdoor','state':'locked','attributes':{}}] if method=='GET' else []
            return httpx.Response(200,json=payload,request=httpx.Request(method,url))
    monkeypatch.setattr(ha.httpx,'Client',FakeClient)
    client.cookies.clear()
    states=client.get('/api/ha/states').json()
    assert [e['id'] for e in states['entities']]==['light.kitchen','sensor.temperature']
    assert client.post('/api/ha/control',json={'entity_id':'light.kitchen','action':'turn_off'}).status_code==200
    assert calls[-1][1]=='http://ha.example.org:8123/api/services/light/turn_off'
    assert calls[-1][2]=={'entity_id':'light.kitchen'}
    for entity,action in [('lock.frontdoor','unlock'),('sensor.temperature','turn_on'),('light.kitchen','toggle')]:
        assert client.post('/api/ha/control',json={'entity_id':entity,'action':action}).status_code==403
    assert client.post('/api/admin/ha/discover',json={}).status_code==401

def test_ha_rejected_token_sanitized(client,monkeypatch):
    from app import home_assistant as ha
    import httpx
    configure_ha(client)
    class FakeClient:
        def __init__(self,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def request(self,*a,**kwargs): return httpx.Response(401,text='secret-ha-token',request=httpx.Request('GET','http://ha.example.org'))
    monkeypatch.setattr(ha.httpx,'Client',FakeClient)
    response=client.get('/api/ha/states')
    assert response.status_code==502 and 'secret-ha-token' not in response.text
    assert client.get('/api/state').status_code==200

def test_ha_host_change_requires_new_token(client):
    configure_ha(client)
    cfg=client.get('/api/admin/settings').json()
    cfg['ha_url']='http://different.example.org'
    assert client.post('/api/admin/settings',json=cfg).status_code==422

@pytest.mark.parametrize('failure,expected,status', [
    ('route','geen netwerkroute',502),
    ('refused','weigert de netwerkverbinding',502),
    ('timeout','10 seconden',504),
    ('html','geen geldige JSON',502),
    ('redirect','ander adres',502),
    ('server','HTTP 503',502),
    ('shape','geldige lijst',502),
])
def test_ha_diagnostic_errors(client, monkeypatch, failure, expected, status):
    from app import home_assistant as ha
    import httpx
    configure_ha(client)
    class FakeClient:
        def __init__(self,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def request(self,*args,**kwargs):
            if failure=='route': raise httpx.ConnectError('[Errno 65] No route to host secret-ha-token')
            if failure=='refused': raise httpx.ConnectError('Connection refused secret-ha-token')
            if failure=='timeout': raise httpx.ConnectTimeout('secret-ha-token')
            request=httpx.Request('GET','http://ha.example.org')
            if failure=='shape': return httpx.Response(200,json={'unexpected':'secret-ha-token'},request=request)
            return httpx.Response({'html':200,'redirect':302,'server':503}[failure],text='secret-ha-token',request=request)
    monkeypatch.setattr(ha.httpx,'Client',FakeClient)
    response=client.get('/api/ha/states')
    assert response.status_code==status and expected in response.json()['detail']
    assert 'secret-ha-token' not in response.text


@pytest.mark.parametrize('service', ['caldav', 'immich'])
def test_changed_endpoint_never_receives_saved_credentials(client, monkeypatch, service):
    old, new = 'https://first.example.test', 'https://second.example.test'
    cfg = client.get('/api/admin/settings').json()
    account = {'id': str(uuid.uuid4()), 'username': 'test', 'url': old, 'password': 'private', 'calendars': []}
    cfg.update(caldav=[account], immich_url=old, immich_key='private')
    assert client.post('/api/admin/settings', json=cfg).status_code == 200

    def unexpected(*args):
        pytest.fail('Discovery must reject the change before making a network call')
    monkeypatch.setattr(integrations, 'discover' if service == 'caldav' else 'albums', unexpected)
    discover = client.post('/api/admin/discover/' + service, json={'id': account['id'], 'url': new})
    assert discover.status_code == 422
    cfg = client.get('/api/admin/settings').json()
    if service == 'caldav':
        cfg['caldav'][0]['url'] = new
    else:
        cfg['immich_url'] = new
    assert client.post('/api/admin/settings', json=cfg).status_code == 422
    with db.connect() as connection:
        current = db.settings(connection)
        assert (current['caldav'][0]['url'], current['caldav'][0]['password']) == (old, 'private')
        assert (current['immich_url'], current['immich_key']) == (old, 'private')
