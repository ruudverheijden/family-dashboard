"""Home Assistant REST adapter. Credentials and arbitrary service access stay private."""
import re
import errno
import ssl
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException

CONTROLLABLE = {'light', 'switch', 'input_boolean'}
ENTITY = re.compile(r'^[a-z_]+\.[a-z0-9_]+$')

def base_url(value):
    p = urlsplit(value)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('', '/'):
        raise ValueError('Gebruik het HA-serveradres zonder dashboardpad, query of inloggegevens.')
    return value.rstrip('/')

def connection_message(error):
    """Classify transport errors without exposing URLs, response bodies or tokens."""
    chain = []
    current = error
    while current is not None and len(chain) < 8:
        chain.append(current)
        current = current.__cause__ or current.__context__
    codes = {getattr(e, 'errno', None) for e in chain}
    # httpcore can retain only a textual errno rather than the original OSError.
    description = ' '.join(str(e).lower() for e in chain)
    if any(isinstance(e, ssl.SSLCertVerificationError) for e in chain) or 'certificate verify failed' in description:
        return 'Het TLS-certificaat van Home Assistant wordt niet vertrouwd. Controleer de certificaatketen en de servernaam; certificaatcontrole blijft ingeschakeld.'
    if codes & {errno.EHOSTUNREACH, errno.ENETUNREACH} or 'no route to host' in description or 'network is unreachable' in description:
        return 'De dashboardserver kan Home Assistant niet bereiken (geen netwerkroute / No route to host). Het token is nog niet gecontroleerd. Controleer lokale netwerktoegang, VPN/firewall en de verbinding van de host. Op macOS kan toestemming voor lokaal netwerk voor Codex of de terminal nodig zijn.'
    if errno.ECONNREFUSED in codes or 'connection refused' in description:
        return 'Home Assistant weigert de netwerkverbinding. Controleer of Home Assistant draait en of de poort klopt. Het token is nog niet gecontroleerd.'
    if 'nodename nor servname' in description or 'name or service not known' in description or 'name resolution' in description:
        return 'De dashboardserver kan de Home Assistant-hostnaam niet vinden. Controleer het adres en DNS. Het token is nog niet gecontroleerd.'
    return 'De dashboardserver kan geen verbinding met Home Assistant maken. Controleer netwerktoegang, serveradres en poort. Het token is nog niet gecontroleerd.'


def request(cfg, method, path, payload=None):
    if not cfg.get('ha_url') or not cfg.get('ha_token'):
        raise HTTPException(409, 'Stel het Home Assistant-serveradres en toegangstoken in via Beheer.')
    try:
        url = base_url(cfg['ha_url'])
    except ValueError:
        raise HTTPException(422, 'Gebruik het Home Assistant-basisadres zonder dashboardpad, query of inloggegevens.')
    try:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.request(method, url + '/api/' + path, headers={'Authorization': 'Bearer ' + cfg['ha_token']}, json=payload)
        if response.status_code in (401, 403):
            raise HTTPException(502, 'Home Assistant weigert het token. Controleer of het geldig is en voldoende rechten heeft.')
        if 300 <= response.status_code < 400:
            raise HTTPException(502, 'Home Assistant verwijst naar een ander adres. Vul het definitieve API-serveradres in; het token wordt niet automatisch doorgestuurd.')
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            raise HTTPException(502, 'Het adres is bereikbaar, maar geeft geen geldige JSON van de Home Assistant-API terug. Controleer het basisadres en eventuele reverse proxy.')
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, 'Home Assistant antwoordt niet binnen 10 seconden. Controleer de netwerkverbinding en of de server beschikbaar is.')
    except httpx.ConnectError as error:
        raise HTTPException(502, connection_message(error))
    except httpx.HTTPStatusError as error:
        raise HTTPException(502, f'Home Assistant geeft HTTP {error.response.status_code} terug. Controleer het API-adres en de server of reverse proxy.')
    except httpx.RequestError:
        raise HTTPException(502, 'De verbinding met Home Assistant is onderbroken. Probeer opnieuw en controleer de netwerkverbinding.')

def clean_state(state):
    attrs = state.get('attributes')
    if not isinstance(attrs, dict):
        attrs = {}
    eid = state['entity_id']
    return {'id': eid, 'name': str(attrs.get('friendly_name') or eid), 'state': str(state.get('state', 'unknown')), 'unit': str(attrs.get('unit_of_measurement') or ''), 'controllable': eid.split('.')[0] in CONTROLLABLE}

def discover(cfg):
    states = request(cfg, 'GET', 'states')
    if not isinstance(states, list):
        raise HTTPException(502, 'De Home Assistant-API geeft geen geldige lijst met entiteiten terug.')
    return [clean_state(s) for s in states if isinstance(s, dict) and isinstance(s.get('entity_id'), str) and ENTITY.fullmatch(s['entity_id'])]

def selected_states(cfg):
    if not cfg.get('ha_entities'):
        return []
    states = {s['id']: s for s in discover(cfg)}
    return [states.get(eid, {'id': eid, 'name': eid, 'state': 'unavailable', 'unit': '', 'controllable': False}) for eid in cfg['ha_entities']]

def control(cfg, entity_id, action):
    if entity_id not in cfg.get('ha_entities', []) or not ENTITY.fullmatch(entity_id):
        raise HTTPException(403, 'Deze entiteit is niet vrijgegeven voor dit scherm.')
    domain = entity_id.split('.')[0]
    if domain not in CONTROLLABLE or action not in ('turn_on', 'turn_off'):
        raise HTTPException(403, 'Deze bediening is niet toegestaan.')
    request(cfg, 'POST', 'services/' + domain + '/' + action, {'entity_id': entity_id})
    return {'ok': True}
