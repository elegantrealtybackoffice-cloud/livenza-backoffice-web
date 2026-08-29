from pathlib import Path
from livenza_booking_core import hash_share_token

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / 'livenza_api_v1.py').read_text(encoding='utf-8')
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')
PAGE = ROOT / 'web' / 'src' / 'app' / 'stays' / 'share' / '[token]' / 'page.tsx'


def test_share_token_hash_is_deterministic_and_not_raw():
    raw = 'parent-secret-token'
    digest = hash_share_token(raw)
    assert digest != raw
    assert len(digest) == 64
    assert digest == hash_share_token(raw)


def test_parent_share_routes_and_hash_only_storage_contract():
    assert '/bookings/<public_id>/parent-share' in API_SOURCE
    assert '/booking-shares/<token>' in API_SOURCE
    block = API_SOURCE.split('def create_parent_share(public_id):', 1)[1].split('\n    @api.', 1)[0]
    assert 'secrets.token_urlsafe(32)' in block
    assert 'hash_share_token(raw_token)' in block
    assert 'token_hash=hash_share_token(raw_token)' in block
    assert 'token_hash=raw_token' not in block


def test_parent_share_owner_and_expiry_are_enforced():
    create = API_SOURCE.split('def create_parent_share(public_id):', 1)[1].split('\n    @api.', 1)[0]
    assert 'booking.customer_id != customer.id' in create
    read = API_SOURCE.split('def get_parent_share(token):', 1)[1].split('\n    @api.', 1)[0]
    assert 'row.expires_at <= now' in read
    assert '410' in read and 'share_expired' in read


def test_public_share_payload_excludes_private_customer_data():
    read = API_SOURCE.split('def get_parent_share(token):', 1)[1].split('\n    @api.', 1)[0]
    for forbidden in ['guardian_json', 'details_json', 'CustomerDocument', 'aadhaar', 'kyc']:
        assert forbidden not in read.lower() if forbidden in {'aadhaar','kyc'} else forbidden not in read
    for published_key in ['safety', 'meals', 'transport', 'policies']:
        assert f'"{published_key}"' in read


def test_parent_share_page_is_honest_about_unpublished_sections():
    assert PAGE.exists()
    text = PAGE.read_text(encoding='utf-8')
    assert 'Not published yet' in text
    assert 'Approve & Pay' in text
