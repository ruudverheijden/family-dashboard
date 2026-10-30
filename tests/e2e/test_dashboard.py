"""Requirement IDs identify acceptance coverage; integration responses are explicit fixtures."""
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from playwright.sync_api import expect
from conftest import login, add_member, save, section, grocery


@pytest.mark.parametrize('size', [(320,740), (740,320), (768,1024), (1024,768), (1440,1000)])
def test_navigation_responsive_UI01_09(dashboard, size):
    p = dashboard
    p.set_viewport_size(dict(zip(('width', 'height'), size)))
    previous = p.locator('.date-nav h2').inner_text()
    p.get_by_role('button', name='Volgende week').click()
    expect(p.locator('.date-nav h2')).not_to_have_text(previous)
    title = p.locator('.date-nav h2').inner_text()
    for tab in ['Home Assistant', 'Immich', 'Kalender']:
        p.get_by_role('navigation', name='Hoofdnavigatie').get_by_role('button', name=tab, exact=True).click()
        for button in p.locator('.main-tabs button').all():
            expect(button).to_be_in_viewport()
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    expect(p.locator('.date-nav h2')).to_have_text(title)
    expect(p.locator('.day-heading').first).to_contain_text('ma')
    for name in ['Taken', 'Routines', 'Boodschappen', 'Beloningen', 'Agenda']:
        section(p, name)
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    for b in p.locator('button:visible').all():
        box = b.bounding_box()
        assert box['width'] >= 48 and box['height'] >= 48, (b.inner_text(), box)


def test_admin_profile_lifecycle_GEZ01_05(dashboard):
    p = dashboard
    assert p.request.get(p.url + 'api/admin/settings').status == 401
    p.get_by_role('button', name='Beheerinstellingen', exact=True).click()
    p.get_by_label('Beheerwachtwoord').fill('wrong-password')
    p.get_by_role('button', name='Ontgrendelen').click()
    expect(p.get_by_role('alert')).to_contain_text('wachtwoord klopt niet')
    p.get_by_label('Beheerwachtwoord').fill('fictional-playwright-password')
    p.get_by_role('button', name='Ontgrendelen').click()
    add_member(p)
    expect(p.locator('[data-member]').filter(has_text='Alex')).to_contain_text('🌻')
    p.get_by_role('button', name='Beheerinstellingen', exact=True).click()
    p.locator('[data-admin-member]').click()
    p.get_by_label('Naam', exact=True).fill('Robin')
    save(p)
    expect(p.locator('[data-member]').filter(has_text='Robin')).to_be_visible()
    p.get_by_role('button', name='Beheerinstellingen', exact=True).click()
    p.get_by_role('button', name='Vergrendelen').click()
    assert p.request.get(p.url + 'api/admin/settings').status == 401
    grocery(p)


def test_grocery_crud_BO01_06(dashboard):
    p = dashboard
    section(p, 'Boodschappen')
    p.get_by_role('button', name='Met details').click()
    p.get_by_label('Wat hebben we nodig?').fill('Appels')
    p.get_by_label('Hoeveelheid').fill('2 kg')
    p.get_by_label('Notitie').fill('Groene')
    save(p)
    row = p.locator('.grocery-row')
    expect(row).to_contain_text('2 kg · Groene')
    p.get_by_role('button', name='Appels bewerken').click()
    p.get_by_label('Wat hebben we nodig?').fill('Peren')
    save(p)
    p.get_by_role('button', name='Vink af Peren').click()
    expect(p.get_by_text('IN HET MANDJE · 1')).to_be_visible()
    p.get_by_role('button', name='Heropen Peren').click()
    expect(p.get_by_text('NOG NODIG · 1')).to_be_visible()
    p.get_by_role('button', name='Peren bewerken').click()
    p.once('dialog', lambda d: d.accept())
    p.get_by_role('button', name='Verwijderen', exact=True).click()
    expect(row).to_have_count(0)
    grocery(p)
    p.get_by_role('button', name='Vink af Melk').click()
    p.once('dialog', lambda d: d.accept())
    p.get_by_role('button', name='Afgevinkte opruimen').click()
    expect(row).to_have_count(0)


def test_two_devices_polling_and_conflict_BO07_08(dashboard, browser, server):
    p = dashboard
    with browser.new_context() as other:
        q = other.new_page()
        q.goto(server)
        section(q, 'Boodschappen')
        grocery(p)
        expect(q.get_by_role('button', name='Vink af Melk')).to_be_visible(timeout=2000)
        p.get_by_role('button', name='Melk bewerken').click()
        p.get_by_label('Notitie').fill('Mijn invoer')
        q.get_by_role('button', name='Melk bewerken').click()
        q.get_by_label('Notitie').fill('Ander apparaat')
        save(q)
        p.get_by_role('button', name='Opslaan', exact=True).click()
        expect(p.get_by_role('alert')).to_contain_text('Je invoer blijft staan')
        expect(p.get_by_label('Notitie')).to_have_value('Mijn invoer')
        assert p.request.get(p.url + 'api/state').json()['groceries'][0]['note'] == 'Ander apparaat'


def test_draft_navigation_and_escape_UI10(dashboard):
    p = dashboard
    section(p, 'Boodschappen')
    p.get_by_role('textbox', name='Boodschap', exact=True).fill('Niet kwijt')
    p.once('dialog', lambda d: d.dismiss())
    p.get_by_role('button', name='Immich', exact=True).click()
    expect(p.get_by_role('textbox', name='Boodschap', exact=True)).to_have_value('Niet kwijt')
    p.get_by_role('button', name='Met details').click()
    p.get_by_label('Notitie').fill('Concept')
    p.once('dialog', lambda d: d.dismiss())
    p.keyboard.press('Escape')
    expect(p.get_by_label('Notitie')).to_have_value('Concept')
    p.once('dialog', lambda d: d.accept())
    p.keyboard.press('Escape')
    expect(p.locator('#dialog')).not_to_be_visible()


@pytest.mark.parametrize('response', ['offline', 'invalid-json', 'server-error'])
def test_failed_save_preserves_input_SYS02(dashboard, response):
    p = dashboard
    section(p, 'Boodschappen')
    p.get_by_role('button', name='Met details').click()
    p.get_by_label('Wat hebben we nodig?').fill('Brood')
    def fail(route):
        if response == 'offline':
            route.abort()
        elif response == 'invalid-json':
            route.fulfill(status=502, body='<html>Error</html>')
        else:
            route.fulfill(status=500, json={'detail': 'Opslaan mislukt'})
    p.route('**/api/entities/groceries', fail)
    p.get_by_role('button', name='Opslaan', exact=True).click()
    expect(p.get_by_role('alert')).to_be_visible()
    expect(p.get_by_label('Wat hebben we nodig?')).to_have_value('Brood')
    assert not p.request.get(p.url + 'api/state').json()['groceries']
    p.unroute('**/api/entities/groceries')
    save(p)
    expect(p.locator('.grocery-row')).to_have_count(1)


@pytest.mark.parametrize('mode,count', [('individual', 2), ('shared', 1)])
def test_task_assignment_repeat_undo_history_TK01_04(dashboard, mode, count):
    p = dashboard
    login(p)
    add_member(p)
    p.get_by_role('button', name='Beheerinstellingen', exact=True).click()
    add_member(p, 'Sam')
    section(p, 'Taken')
    p.get_by_role('button', name='Nieuwe taak', exact=True).click()
    p.get_by_label('Titel', exact=True).fill('Tafel dekken')
    p.get_by_label('Beschrijving').fill('Voor het ontbijt')
    p.get_by_label('Alex', exact=True).check()
    p.get_by_label('Sam', exact=True).check()
    p.get_by_label('Uitvoering').select_option(mode)
    p.get_by_label('Herhaling').select_option('daily')
    p.get_by_label('Punten').fill('5')
    save(p)
    expect(p.locator('.task-row')).to_have_count(count)
    p.get_by_role('button', name='Voltooi Tafel dekken').first.click()
    expect(p.get_by_role('button', name='Heropen Tafel dekken')).to_have_count(1)
    p.reload()
    section(p, 'Taken')
    expect(p.get_by_role('button', name='Heropen Tafel dekken')).to_have_count(1)
    p.get_by_role('button', name='Volgende dag').click()
    expect(p.get_by_role('button', name='Voltooi Tafel dekken')).to_have_count(count)
    p.get_by_role('button', name='Vorige dag').click()
    p.get_by_role('button', name='Heropen Tafel dekken').click()
    expect(p.get_by_role('button', name='Voltooi Tafel dekken')).to_have_count(count)
    p.locator('[data-member]').filter(has_text='Alex').click()
    expect(p.locator('.task-row')).to_have_count(1)
    p.get_by_role('button', name='Historie bekijken').click()
    expect(p.locator('.history-item').filter(has_text='Voortgang')).to_have_count(2)


def test_task_edit_updates_overview(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, 'Taken')
    p.get_by_role('button', name='Nieuwe taak', exact=True).click()
    p.get_by_label('Titel', exact=True).fill('Oude titel')
    p.get_by_label('Alex', exact=True).check()
    save(p)
    row = p.locator('.task-row')
    expect(row).to_contain_text('Oude titel')

    p.get_by_role('button', name='Taak bewerken').click()
    p.get_by_label('Titel', exact=True).fill('Nieuwe titel')
    p.get_by_label('Beschrijving').fill('Bijgewerkte beschrijving')
    save(p)

    expect(row).to_contain_text('Nieuwe titel')
    expect(row).to_contain_text('Bijgewerkte beschrijving')
    expect(row).not_to_contain_text('Oude titel')


def test_routine_progress_new_day_RT01_04(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, 'Routines')
    p.get_by_role('button', name='Nieuwe routine', exact=True).click()
    p.get_by_label('Titel', exact=True).fill('Ochtend')
    p.get_by_label('Alex', exact=True).check()
    p.get_by_label('Stappen, één per regel').fill('🪥 | Poetsen\n🎒 | Tas inpakken')
    save(p)
    expect(p.locator('.step')).to_have_text(['🪥 Poetsen', '🎒 Tas inpakken'])
    p.get_by_role('button', name='Voltooi Poetsen').click()
    expect(p.get_by_text('1 van 2 stappen klaar')).to_be_visible()
    p.reload()
    section(p, 'Routines')
    expect(p.get_by_role('button', name='Heropen Poetsen')).to_be_visible()
    p.get_by_role('button', name='Volgende dag').click()
    expect(p.get_by_text('0 van 2 stappen klaar')).to_be_visible()
    p.get_by_role('button', name='Vorige dag').click()
    expect(p.get_by_text('1 van 2 stappen klaar')).to_be_visible()


def test_ha_custom_dashboard_is_embedded_without_entity_api(dashboard):
    p = dashboard
    requests = []
    p.on('request', lambda request: requests.append(request.url))
    p.route('http://homeassistant.example.test:8123/**', lambda route: route.fulfill(content_type='text/html', body='<h1>Mijn HA-dashboard</h1>'))
    login(p)
    p.get_by_label('Serveradres', exact=True).fill('http://homeassistant.example.test:8123')
    p.get_by_label('Dashboardpad', exact=True).fill('/dashboard-family/overview')
    p.get_by_role('button', name='Instellingen opslaan').click()
    expect(p.locator('#dialog')).not_to_be_visible()
    p.get_by_role('button', name='Home Assistant', exact=True).click()
    frame = p.locator('#ha-dashboard')
    expect(frame).to_be_visible()
    expect(frame).to_have_attribute('src', 'http://homeassistant.example.test:8123/dashboard-family/overview')
    expect(p.get_by_role('link', name='Home Assistant openen in een nieuw tabblad')).to_have_attribute('href', 'http://homeassistant.example.test:8123/dashboard-family/overview')
    assert not p.locator('[data-ha-entity]').count()
    assert not any('/api/ha/' in url for url in requests)
    expect(p.frame_locator('#ha-dashboard').get_by_role('heading', name='Mijn HA-dashboard')).to_be_visible()


def photos(p):
    def state(route):
        response = route.fetch()
        body = response.json()
        body['photos'] = [{'id': 'one', 'album':'Testalbum'}, {'id':'two', 'album':'Testalbum'}]
        route.fulfill(response=response, json=body)
    p.route('**/api/state*', state)
    p.route('**/api/photos/*', lambda r: r.fulfill(content_type='image/svg+xml', body='<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><rect width="100" height="50" fill="green"/></svg>'))
    p.reload()
    expect(p.get_by_role('heading', name='Ruimte voor het dagelijks leven.')).to_be_visible()


def test_slideshow_controls_failure_IM02_06_10_12(dashboard):
    p = dashboard
    photos(p)
    p.get_by_role('button', name='Immich', exact=True).click()
    expect(p.locator('#photo')).to_have_attribute('src', '/api/photos/one')
    expect(p.locator('#photo')).to_have_css('object-fit', 'contain')
    p.get_by_role('button', name='Volgende foto').click()
    expect(p.locator('#photo')).to_have_attribute('src', '/api/photos/two')
    p.get_by_role('button', name='Vorige foto').click()
    p.get_by_role('button', name='Diavoorstelling pauzeren').click()
    p.clock.install()
    p.clock.fast_forward(31000)
    expect(p.locator('#photo')).to_have_attribute('src', '/api/photos/one')
    p.locator('#photo').click()
    expect(p.locator('[data-tab=photos]')).to_have_class('active')
    p.route('**/api/photos/*', lambda r: r.fulfill(status=404))
    p.reload()
    p.get_by_role('button', name='Immich', exact=True).click()
    expect(p.get_by_text('De foto’s zijn momenteel niet beschikbaar. Probeer het later opnieuw.')).to_be_visible()


@pytest.mark.parametrize('guard', ['none', 'draft', 'dialog', 'routine'])
def test_idle_guards_IM09_11(dashboard, guard):
    p = dashboard
    photos(p)
    p.get_by_role('button', name='Dit scherm instellen').click()
    p.get_by_label('Na inactiviteit').fill('1')
    p.get_by_role('button', name='Opslaan op dit scherm').click()
    expect(p.locator('#dialog')).not_to_be_visible()
    if guard == 'draft':
        section(p, 'Boodschappen')
        p.get_by_role('textbox', name='Boodschap', exact=True).fill('Concept')
    elif guard == 'dialog':
        p.get_by_role('button', name='Dit scherm instellen').click()
    elif guard == 'routine':
        section(p, 'Routines')
    p.clock.install()
    p.clock.fast_forward(61000)
    expect(p.locator('[data-tab=photos]' if guard == 'none' else '[data-tab=calendar]')).to_have_class('active')


def test_preferences_local_SYS08(dashboard, browser, server):
    p = dashboard
    p.get_by_role('button', name='Dit scherm instellen').click()
    p.get_by_label('Na inactiviteit').fill('3')
    p.get_by_label('Foto’s beeldvullend uitsnijden').check()
    p.get_by_role('button', name='Opslaan op dit scherm').click()
    expect(p.locator('#dialog')).not_to_be_visible()
    p.reload()
    p.get_by_role('button', name='Dit scherm instellen').click()
    expect(p.get_by_label('Na inactiviteit')).to_have_value('3')
    expect(p.get_by_label('Foto’s beeldvullend uitsnijden')).to_be_checked()
    with browser.new_context() as other:
        q = other.new_page()
        q.goto(server)
        q.get_by_role('button', name='Dit scherm instellen').click()
        expect(q.get_by_label('Na inactiviteit')).to_have_value('0')
        expect(q.get_by_label('Foto’s beeldvullend uitsnijden')).not_to_be_checked()


def test_keyboard_and_xss_UI07_SYS04(dashboard):
    p = dashboard
    grocery(p, '<img src=x onerror=alert(1)>')
    expect(p.locator('.grocery-row img')).to_have_count(0)
    p.get_by_role('button', name='Met details').focus()
    p.keyboard.press('Enter')
    expect(p.locator('#dialog')).to_be_visible()
    p.get_by_label('Wat hebben we nodig?').fill('Toetsenbord')
    p.keyboard.press('Enter')
    expect(p.get_by_role('button', name='Vink af Toetsenbord')).to_be_visible()
    p.get_by_role('button', name='Vink af Toetsenbord').focus()
    expect(p.get_by_role('button', name='Vink af Toetsenbord')).to_have_css('outline-style', 'solid')
    p.keyboard.press('Space')
    expect(p.get_by_role('button', name='Heropen Toetsenbord')).to_be_visible()


def test_calendar_timezone_filter_AG01_04(dashboard):
    p = dashboard
    def calendar(route):
        response = route.fetch()
        body = response.json()
        body['day'] = '2026-10-25'
        body['members'] = [{'id':'alex', 'name':'Alex', 'color':'#aa7755', 'avatar':'🌻'}, {'id':'sam', 'name':'Sam', 'color':'#5577aa', 'avatar':''}]
        body['events'] = [
            {'title':'Voor wintertijd', 'start':'2026-10-25T00:30:00Z', 'end':'2026-10-25T00:45:00Z', 'member':'alex', 'calendar':'Gezin', 'all_day':False},
            {'title':'Na wintertijd', 'start':'2026-10-25T01:30:00Z', 'end':'2026-10-25T01:45:00Z', 'member':'sam', 'calendar':'Gezin', 'all_day':False},
            {'title':'Hele dag samen', 'start':'2026-10-24', 'end':'2026-10-26', 'member':'', 'calendar':'Gezin', 'all_day':True}]
        route.fulfill(response=response, json=body)
    p.route('**/api/state*', calendar)
    p.reload()
    p.get_by_role('button', name='Selecteer 25 oktober').click()
    p.get_by_role('button', name='Dag', exact=True).click()
    expect(p.locator('.event time')).to_have_text(['Hele dag', '02:30', '02:30'])
    p.locator('[data-member=alex]').click()
    expect(p.locator('.event')).to_have_count(2)
    expect(p.locator('.event').filter(has_text='Na wintertijd')).to_have_count(0)


def test_lost_response_retry_no_duplicate_BO08(dashboard):
    p = dashboard
    section(p, 'Boodschappen')
    def lost(route):
        response = route.fetch()
        assert response.ok
        route.abort()
    p.route('**/api/entities/groceries', lost, times=1)
    p.get_by_role('textbox', name='Boodschap', exact=True).fill('Een brood')
    p.get_by_role('button', name='Toevoegen', exact=True).click()
    expect(p.locator('#toast')).to_contain_text('niet bevestigd')
    p.get_by_role('button', name='Toevoegen', exact=True).click()
    expect(p.locator('.grocery-row')).to_have_count(1)
    assert len(p.request.get(p.url + 'api/state').json()['groceries']) == 1


def test_simultaneous_completion_SYS03(dashboard, browser, server):
    p = dashboard
    login(p)
    add_member(p)
    section(p, 'Taken')
    p.get_by_role('button', name='Nieuwe taak', exact=True).click()
    p.get_by_label('Titel', exact=True).fill('Samen opruimen')
    p.get_by_label('Alex', exact=True).check()
    p.get_by_label('Uitvoering').select_option('shared')
    save(p)
    with browser.new_context() as other:
        q = other.new_page()
        q.goto(server)
        section(q, 'Taken')
        pending = []
        def hold(route):
            pending.append((route, route.request.post_data_json))
        p.route('**/api/entities/runs', hold)
        q.route('**/api/entities/runs', hold)
        p.get_by_role('button', name='Voltooi Samen opruimen').click()
        q.get_by_role('button', name='Voltooi Samen opruimen').click()
        expect(q.get_by_role('button', name='Voltooi Samen opruimen')).to_be_disabled()
        assert len(pending) == 2
        def send(entry):
            return httpx.post(server + '/api/entities/runs', json=entry[1], headers={'X-Family-Request':'1'})
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(send, pending))
        for (route, _), response in zip(pending, responses):
            assert response.status_code == 200
            route.fulfill(status=response.status_code, body=response.text, content_type='application/json')
        expect(p.get_by_role('button', name='Heropen Samen opruimen')).to_be_visible()
        expect(q.get_by_role('button', name='Heropen Samen opruimen')).to_be_visible()
        history = p.request.get(p.url + 'api/history').json()
        assert len([h for h in history if h['kind'] == 'runs']) == 1


def test_backend_disconnect_recovers_SYS02(dashboard):
    p = dashboard
    p.route('**/api/state*', lambda r: r.abort())
    expect(p.locator('#connection')).to_be_visible()
    p.unroute('**/api/state*')
    expect(p.locator('#connection')).not_to_be_visible()


def test_points_reward_request_and_parent_approval_BEL01_05(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, 'Taken')
    p.get_by_role('button', name='Nieuwe taak', exact=True).click()
    p.get_by_label('Titel', exact=True).fill('Bed opmaken')
    p.get_by_label('Alex', exact=True).check()
    p.get_by_label('Punten bij voltooien').fill('5')
    save(p)
    p.get_by_role('button', name='Voltooi Bed opmaken').click()

    section(p, 'Beloningen')
    p.locator('[data-member]').filter(has_text='Alex').click()
    expect(p.get_by_text('5 beschikbaar', exact=False)).to_be_visible()
    p.get_by_role('button', name='Beheerinstellingen', exact=True).click()
    p.get_by_role('button', name='Beloning toevoegen').click()
    p.get_by_label('Naam', exact=True).fill('Filmavond')
    p.get_by_label('Prijs in punten').fill('4')
    save(p)

    section(p, 'Beloningen')
    p.get_by_role('button', name='Aanvragen').click()
    expect(p.get_by_text('4 gereserveerd', exact=False)).to_be_visible()
    expect(p.get_by_text('In afwachting')).to_be_visible()

    p.get_by_role('button', name='Beheerinstellingen', exact=True).click()
    p.get_by_role('button', name='Goedkeuren').click()
    expect(p.get_by_text('Beloning goedgekeurd; punten afgeschreven.')).to_be_visible()
    p.get_by_role('button', name='Sluiten').click()
    section(p, 'Beloningen')
    expect(p.get_by_text('1 beschikbaar', exact=False)).to_be_visible()
    expect(p.get_by_text('Goedgekeurd', exact=True)).to_be_visible()
