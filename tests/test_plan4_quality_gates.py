from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/'web/scripts/check-route-sources.mjs').read_text(encoding='utf-8')
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')


def test_route_audit_covers_store_and_my_livenza_v1_routes():
    for route in ['store/cart','store/checkout','my/orders','my/rewards']:
        assert route in SCRIPT


def test_frontend_never_contains_razorpay_webhook_secret_or_key_secret():
    web=ROOT/'web/src'
    text='\n'.join(path.read_text(encoding='utf-8',errors='ignore') for path in web.rglob('*') if path.is_file())
    assert 'RAZORPAY_KEY_SECRET' not in text
    assert 'RAZORPAY_WEBHOOK_SECRET' not in text
    assert 'webhook_secret' not in text


def test_store_public_contract_has_no_client_discount_authority():
    block=API.split('def create_store_order(',1)[1].split('\n    @api.',1)[0]
    assert 'discount_minor=0' in block
    assert 'payload.get("discount' not in block and "payload.get('discount" not in block
