from pathlib import Path
from livenza_receipts import receipt_number, build_receipt_view

ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')


def test_receipt_number_is_deterministic():
    assert receipt_number('booking-public','payment-public') == receipt_number('booking-public','payment-public')
    assert receipt_number('booking-public','payment-public').startswith('LVZ-R-')


def test_receipt_view_contains_only_transactional_fields():
    view=build_receipt_view(
        booking_id='B1', payment_id='P1', property_name='Oasis Residency',
        amount_minor=125000, currency='INR', paid_at='2026-09-01T10:00:00Z'
    )
    assert view['booking_id']=='B1' and view['amount_minor']==125000
    assert 'guardian' not in view and 'kyc' not in view


def test_receipt_endpoint_is_owner_scoped_and_only_for_paid_booking():
    assert '/bookings/<public_id>/receipt' in API
    block=API.split('def booking_receipt(public_id):',1)[1].split('\n    @api.',1)[0]
    assert 'customer_id=customer.id' in block
    assert 'payment.status != "paid"' in block
