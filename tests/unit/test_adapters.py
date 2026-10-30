import pytest
from app import home_assistant as ha, integrations


def test_selection_preserves_order_filters_private_and_handles_missing(monkeypatch):
    states = [
        {'entity_id': 'sensor.private', 'state': 'private'},
        {'entity_id': 'sensor.temp', 'state': '21', 'attributes': {'unit_of_measurement': '°C'}},
        {'entity_id': 'light.room', 'state': 'on', 'attributes': 'malformed'},
        {'entity_id': 'invalid id'}, None,
    ]
    monkeypatch.setattr(ha, 'request', lambda *_: states)
    selected = ha.selected_states({'ha_entities': ['light.room', 'switch.missing', 'sensor.temp']})
    assert [(s['id'], s['state'], s['controllable']) for s in selected] == [
        ('light.room', 'on', True), ('switch.missing', 'unavailable', False), ('sensor.temp', '21', False)]
    assert selected[0]['name'] == 'light.room'
    assert selected[2]['unit'] == '°C'


def test_empty_selection_does_not_contact_ha(monkeypatch):
    monkeypatch.setattr(ha, 'request', lambda *_: pytest.fail('unexpected network request'))
    assert ha.selected_states({'ha_entities': []}) == []


@pytest.mark.parametrize('new_url', [
    'http://other.test/dav', 'http://old.test:8080/dav', 'https://old.test/dav', 'http://old.test/proxy',
])
def test_saved_secret_is_bound_to_address(new_url):
    old = 'http://old.test/dav'
    with pytest.raises(ValueError):
        integrations.endpoint_secret(old, new_url, 'old-secret', '')
    assert integrations.endpoint_secret(old, new_url, 'old-secret', 'replacement') == 'replacement'


def test_trailing_slash_can_reuse_secret():
    assert integrations.endpoint_secret('https://example.test/dav/', 'https://example.test/dav', 'saved', '') == 'saved'


def test_removing_endpoint_also_forgets_credential():
    assert integrations.endpoint_secret('https://example.test', '', 'saved', '') == ''
