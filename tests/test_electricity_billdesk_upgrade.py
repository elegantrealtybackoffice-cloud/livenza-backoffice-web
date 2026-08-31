from types import SimpleNamespace

from electricity_core import fetch_bill_from_billdesk
from electricity_providers import electricity_city_choices


class FakeResponse:
    ok = True
    status_code = 200
    def __init__(self, payload):
        self._payload = payload
    def json(self):
        return self._payload


class FakeHTTP:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []
    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.payload)


def _connection():
    return SimpleNamespace(
        identifier_primary='211584066201',
        identifier_primary_type='K_NO',
        identifier_secondary='',
    )


def _provider():
    return SimpleNamespace(
        name='Jaipur Vidyut Vitran Nigam Limited (JVVNL)',
        bbps_biller_id='',
        supports_bbps_fetch=True,
    )


def test_billdesk_requires_merchant_api_configuration():
    result = fetch_bill_from_billdesk(_connection(), _provider(), {})
    assert result['ok'] is False
    assert result['status'] == 'integration_not_configured'
    assert 'BillDesk API' in result['message']


def test_billdesk_fetch_posts_k_number_and_normalizes_nested_bill():
    http = FakeHTTP({
        'response': {
            'billDetails': {
                'consumerName': 'M/S SPYTECH BUILDCON',
                'billNumber': 'JVVNL-2026-08-123',
                'billDate': '31/08/2026',
                'dueDate': '10/09/2026',
                'amountDue': '12,345.67',
                'meterNo': '22103435',
                'units': '456',
            }
        }
    })
    config = {
        'fetch_url': 'https://merchant-api.example/bharat-connect/bill-fetch',
        'client_id': 'client-1',
        'client_secret': 'secret-1',
        'merchant_id': 'livenza',
        'biller_id': 'jvvnl-from-onboarding',
    }
    result = fetch_bill_from_billdesk(_connection(), _provider(), config, http=http)
    assert result['ok'] is True
    assert result['bill']['total_due_amount'] == '12345.67'
    assert result['bill']['consumer_name'] == 'M/S SPYTECH BUILDCON'
    assert result['bill']['due_date'] == '2026-09-10'
    assert result['bill']['meter_number'] == '22103435'
    assert result['bill']['identifier_primary'] == '211584066201'
    assert len(http.calls) == 1
    url, kwargs = http.calls[0]
    assert url == config['fetch_url']
    assert kwargs['json']['consumer_identifier'] == '211584066201'
    assert kwargs['json']['identifier_type'] == 'K_NO'
    assert kwargs['json']['biller_id'] == 'jvvnl-from-onboarding'
    assert kwargs['json']['merchant_id'] == 'livenza'


def test_billdesk_supports_configurable_auth_headers():
    http = FakeHTTP({'bill': {'amount': '500', 'dueDate': '2026-09-05'}})
    config = {
        'fetch_url': 'https://merchant-api.example/fetch',
        'client_id': 'abc',
        'client_secret': 'def',
        'api_key': 'key-123',
        'auth_header': 'X-BD-Authorization',
        'auth_prefix': 'Token',
        'api_key_header': 'X-BD-Api-Key',
        'client_id_header': 'X-BD-Client-Id',
        'biller_id': 'JVVNL',
    }
    result = fetch_bill_from_billdesk(_connection(), _provider(), config, http=http)
    assert result['ok'] is True
    _, kwargs = http.calls[0]
    assert kwargs['headers']['X-BD-Authorization'] == 'Token def'
    assert kwargs['headers']['X-BD-Api-Key'] == 'key-123'
    assert kwargs['headers']['X-BD-Client-Id'] == 'abc'
    assert 'secret' not in str(result['raw_meta']).lower()


def test_city_choices_include_livenza_provider_coverage_and_jvvnl_districts():
    city_rows = [SimpleNamespace(id=1, name='Jaipur'), SimpleNamespace(id=2, name='Gurugram')]
    providers = [
        SimpleNamespace(state='Rajasthan', city='Jaipur / JVVNL Area', name='Jaipur Vidyut Vitran Nigam Limited (JVVNL)'),
        SimpleNamespace(state='Haryana', city='Gurugram / South Haryana', name='DHBVN'),
    ]
    choices = electricity_city_choices(city_rows, providers)
    labels = [x['label'] for x in choices]
    assert 'Jaipur' in labels
    assert 'Gurugram' in labels
    assert 'Dausa' in labels
    assert 'Alwar' in labels
    assert 'Tonk' in labels
    assert 'Karauli' in labels
    assert 'Jaipur / JVVNL Area' in labels
    assert 'Gurugram / South Haryana' in labels
    assert len(labels) == len(set(labels))
