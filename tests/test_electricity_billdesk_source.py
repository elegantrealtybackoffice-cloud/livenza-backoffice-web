from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
HTML=(ROOT/'templates'/'electricity.html').read_text(encoding='utf-8')
JS=(ROOT/'static'/'electricity.js').read_text(encoding='utf-8')
ENV=(ROOT/'.env.example').read_text(encoding='utf-8')
SEED=(ROOT/'data'/'electricity_providers_india.json').read_text(encoding='utf-8')


def test_app_routes_jvvnl_fetch_through_billdesk_adapter():
    assert 'fetch_bill_from_billdesk' in APP
    assert 'BILLDESK_BILL_FETCH_URL' in APP
    assert "'billdesk_bharat_connect'" in APP
    assert 'BillDesk / Bharat Connect' in APP


def test_electricity_city_selector_uses_expanded_city_choices():
    assert 'city_choices' in APP
    assert 'name="city_choice"' in HTML
    assert 'electricityCitySearch' in HTML
    assert 'electricityCitySelect' in HTML
    assert 'filterSelectOptions' in JS


def test_jvvnl_seed_is_billdesk_ready_without_hardcoding_private_api():
    assert 'https://pay.billdesk.com/instapayweb/jvvnl' in SEED
    assert '"supports_bbps_fetch": true' in SEED
    assert 'BILLDESK_BILL_FETCH_URL' in ENV
    assert 'BILLDESK_JVVNL_BILLER_ID' in ENV
    assert 'merchant-api.example' not in APP
