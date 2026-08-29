from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
CLIENT=(ROOT/'web/src/components/booking/parent-share-payment.tsx')
WEBAPI=(ROOT/'web/src/lib/api.ts').read_text(encoding='utf-8')


def test_parent_share_payment_endpoint_exists_and_requires_login():
    assert '/booking-shares/<token>/payments' in API
    block=API.split('def create_parent_share_payment(token):',1)[1].split('\n    @api.',1)[0]
    assert 'session_for_request()' in block
    assert 'authentication_required' in block
    assert 'hash_share_token(token)' in block
    assert 'row.expires_at <= now' in block


def test_parent_payment_remains_owned_by_booking_customer():
    block=API.split('def create_parent_share_payment(token):',1)[1].split('\n    @api.',1)[0]
    assert 'customer_id=booking.customer_id' in block
    assert 'payer_customer_public_id' in block
    assert 'payer_mobile' in block


def test_parent_share_page_has_real_payment_client():
    assert CLIENT.exists()
    text=CLIENT.read_text(encoding='utf-8')
    assert 'createParentPayment' in text
    assert 'loadRazorpay' in text
    assert 'Approve & Pay' in text
    assert 'getMe' in text
    assert 'function createParentPayment' in WEBAPI
