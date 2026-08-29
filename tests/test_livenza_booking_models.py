from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')
TREE = ast.parse(APP_SOURCE)
CLASS_NAMES = {node.name for node in TREE.body if isinstance(node, ast.ClassDef)}

BOOKING_MODELS = [
    'StayRatePlan', 'StayInventoryHold', 'StayBooking', 'StayBookingItem',
    'BookingAddOn', 'PaymentRecord', 'ProcessedWebhookEvent',
    'CustomerDocument', 'SupportTicket', 'BookingShareToken',
]

def test_booking_and_payment_models_exist_in_source():
    missing = [name for name in BOOKING_MODELS if name not in CLASS_NAMES]
    assert not missing, f'missing models: {missing}'


def test_webhook_event_key_is_unique_in_source():
    block = APP_SOURCE.split('class ProcessedWebhookEvent', 1)[1].split('\nclass ', 1)[0]
    assert 'external_event_id' in block
    assert 'unique=True' in block


def test_hold_has_expiry_and_state_indexes_in_source():
    block = APP_SOURCE.split('class StayInventoryHold', 1)[1].split('\nclass ', 1)[0]
    assert 'expires_at' in block and 'index=True' in block
    assert 'status' in block and 'index=True' in block


def test_booking_migration_is_additive_and_creates_required_tables():
    path = ROOT / 'migrations' / 'livenza_v1_booking_payments.sql'
    assert path.exists()
    sql = path.read_text(encoding='utf-8').upper()
    assert 'DROP TABLE' not in sql and 'DROP COLUMN' not in sql
    for table in [
        'stay_rate_plan','stay_inventory_hold','stay_booking','stay_booking_item',
        'booking_add_on','payment_record','processed_webhook_event',
        'customer_document','support_ticket','booking_share_token',
    ]:
        assert table.upper() in sql


def test_runtime_booking_model_contracts_when_flask_is_available(app_module):
    assert app_module.ProcessedWebhookEvent.__table__.columns['external_event_id'].unique
    assert 'expires_at' in app_module.StayInventoryHold.__table__.columns
    assert 'status' in app_module.StayInventoryHold.__table__.columns
