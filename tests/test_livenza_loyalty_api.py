from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
APP=(ROOT/'app.py').read_text(encoding='utf-8')
REWARDS=(ROOT/'web/src/app/my/rewards/page.tsx')
ORDERS=(ROOT/'web/src/app/my/orders/page.tsx')
DASH=(ROOT/'web/src/components/my/my-dashboard.tsx').read_text(encoding='utf-8')


def _block(name): return API.split(f'def {name}(',1)[1].split('\n    @api.',1)[0]


def test_rewards_api_is_owner_scoped_and_ledger_derived():
    assert '/me/rewards' in API
    block=_block('my_rewards')
    assert 'session_for_request()' in block
    assert 'LoyaltyLedgerEntry' in block
    assert 'balance(' in block


def test_loyalty_award_is_idempotent_by_source_effect():
    block=_block('_award_loyalty_points')
    assert 'source_type=source_type' in block
    assert 'source_id=source_id' in block
    assert 'effect_key=effect_key' in block
    assert 'existing' in block
    assert 'LIVENZA_POINTS_PER_100_INR' in block


def test_paid_booking_and_store_confirmation_trigger_independent_awards():
    block=_block('_confirm_payment_source')
    assert 'stay_booking_paid' in block
    assert 'store_order_paid' in block
    assert '_award_loyalty_points' in block


def test_my_orders_api_and_pages_exist():
    assert '/me/orders' in API
    assert REWARDS.exists()
    assert ORDERS.exists()
    assert 'Livenza+' in DASH
    assert '/my/orders' in DASH and '/my/rewards' in DASH
