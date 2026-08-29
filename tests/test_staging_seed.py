from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / 'livenza_staging_seed.py'
    spec = importlib.util.spec_from_file_location('livenza_staging_seed', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_seed_spec_is_clearly_staging_only_and_contains_stays_store_data():
    module = _load_module()
    spec = module.staging_seed_spec()
    assert spec['properties']
    assert spec['products']
    assert {p['city'] for p in spec['properties']} == {'Jaipur', 'Gurugram'}
    assert all(p['name'].startswith('[STAGING]') for p in spec['properties'])
    assert all(p['slug'].startswith('staging-') for p in spec['properties'])
    assert all(product['name'].startswith('[STAGING]') for product in spec['products'])
    assert all(product['slug'].startswith('staging-') for product in spec['products'])


def test_seed_spec_contains_allocatable_inventory_rate_plans_and_stock():
    module = _load_module()
    spec = module.staging_seed_spec()
    for prop in spec['properties']:
        assert prop['categories']
        for category in prop['categories']:
            assert category['units'] >= 1
            assert category['rate_plans']
            assert all(plan['amount_minor'] > 0 for plan in category['rate_plans'])
    assert all(v['stock_on_hand'] > 0 for p in spec['products'] for v in p['variants'])


def test_seed_spec_has_no_customer_or_live_secret_payloads():
    module = _load_module()
    text = repr(module.staging_seed_spec()).lower()
    for forbidden in ('customer_mobile', 'aadhaar', 'razorpay_key', 'database_url', 'secret_key', 'whatsapp_token'):
        assert forbidden not in text


def test_admin_seed_route_is_admin_only_staging_only_and_confirmed():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "@app.route('/admin/livenza/staging/seed',methods=['GET','POST'])" in source
    assert '@admin_required' in source[source.index("@app.route('/admin/livenza/staging/seed'"):][:500]
    route_block = source[source.index("def livenza_staging_seed_admin"):source.index("def livenza_staging_seed_admin") + 2500]
    assert "LIVENZA_ENV" in route_block
    assert "abort(404)" in route_block
    assert "SEED STAGING" in route_block
    assert "seed_staging_data" in route_block
