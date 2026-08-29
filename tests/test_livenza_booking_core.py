from datetime import date, datetime, timezone
import pytest

from livenza_booking_core import (
    validate_booking_dates, hold_expiry, amount_due_now,
    transition_booking, transition_hold, overlaps,
)


def test_booking_date_range_must_be_positive():
    assert validate_booking_dates('2026-09-01', '2026-10-01') == (date(2026,9,1), date(2026,10,1))
    with pytest.raises(ValueError):
        validate_booking_dates('2026-10-01', '2026-09-01')


def test_reserve_collects_configured_reservation_amount_only():
    assert amount_due_now('reserve', 16_000_000, 1_000_000) == 1_000_000
    assert amount_due_now('book_now', 16_000_000, 1_000_000) == 16_000_000
    with pytest.raises(ValueError):
        amount_due_now('reserve', 16_000_000, 0)


def test_booking_and_hold_transitions_reject_illegal_jumps():
    assert transition_booking('held', 'payment_started') == 'pending_payment'
    assert transition_booking('pending_payment', 'payment_paid') == 'confirmed'
    with pytest.raises(ValueError):
        transition_booking('cancelled', 'payment_paid')
    assert transition_hold('active', 'booking_confirmed') == 'converted'


def test_hold_expiry_is_timezone_safe_and_positive():
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    assert hold_expiry(now, 10).isoformat() == '2026-09-01T10:10:00+00:00'
    with pytest.raises(ValueError):
        hold_expiry(now, 0)


def test_date_overlap_uses_half_open_intervals():
    assert overlaps(date(2026,9,1), date(2026,9,10), date(2026,9,9), date(2026,9,12))
    assert not overlaps(date(2026,9,1), date(2026,9,10), date(2026,9,10), date(2026,9,12))
