from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / 'livenza_api_v1.py').read_text(encoding='utf-8')
INVENTORY_SOURCE = (ROOT / 'livenza_inventory_core.py').read_text(encoding='utf-8')
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_booking_routes_and_no_availability_code_exist():
    for route in ['/bookings/hold', '/bookings', '/bookings/<public_id>']:
        assert route in API_SOURCE
    assert 'NO_AVAILABILITY' in API_SOURCE


def test_hold_route_requires_authenticated_customer():
    block = API_SOURCE.split('def booking_hold()', 1)[1].split('\n    @api.', 1)[0]
    assert 'session_for_request()' in block
    assert 'authentication_required' in block


def test_postgres_hold_selection_uses_row_locking():
    assert 'with_for_update(skip_locked=True)' in API_SOURCE


def test_booking_creation_checks_hold_owner_expiry_and_state():
    block = API_SOURCE.split('def create_booking()', 1)[1].split('\n    @api.', 1)[0]
    for text in ['hold.customer_id != customer.id', "hold.status != 'active'", 'hold.expires_at <= now']:
        assert text in block
    assert 'amount_due_now(' in block


def test_availability_subtracts_active_holds_and_confirmed_bookings():
    block = API_SOURCE.split('def public_availability()', 1)[1].split('\n    app.register_blueprint', 1)[0]
    assert 'StayInventoryHold' in block
    assert 'StayBookingItem' in block
    assert 'StayBooking' in block
    assert 'available_count' in block


def test_api_registration_injects_booking_models():
    for name in ['StayRatePlan','StayInventoryHold','StayBooking','StayBookingItem','BookingAddOn']:
        assert f"'{name}': {name}" in APP_SOURCE


def test_runtime_hold_requires_authentication_when_flask_is_available(client):
    res = client.post('/api/v1/bookings/hold', json={})
    assert res.status_code == 401

def test_booking_addon_prices_are_server_controlled():
    block = API_SOURCE.split('def create_booking()', 1)[1].split('\n    @api.', 1)[0]
    assert '_booking_addon_catalog()' in block
    assert 'item.get("amount_minor")' not in block
    assert '/booking-addons' in API_SOURCE
