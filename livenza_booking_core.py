"""Pure booking lifecycle helpers for Livenza.life V1."""
from __future__ import annotations

from datetime import date, datetime, timedelta

BOOKING_TRANSITIONS = {
    ("held", "payment_started"): "pending_payment",
    ("held", "cancel"): "cancelled",
    ("held", "expire"): "expired",
    ("pending_payment", "payment_paid"): "confirmed",
    ("pending_payment", "payment_failed"): "held",
    ("pending_payment", "expire"): "expired",
    ("confirmed", "cancel"): "cancelled",
}

HOLD_TRANSITIONS = {
    ("active", "booking_confirmed"): "converted",
    ("active", "expire"): "expired",
    ("active", "release"): "released",
}


def _as_date(value) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError("dates must use YYYY-MM-DD") from exc
    raise ValueError("dates must use YYYY-MM-DD")


def validate_booking_dates(start, end) -> tuple[date, date]:
    start_date = _as_date(start)
    end_date = _as_date(end)
    if end_date <= start_date:
        raise ValueError("end must be after start")
    return start_date, end_date


def hold_expiry(now: datetime, minutes: int) -> datetime:
    try:
        duration = int(minutes)
    except (TypeError, ValueError) as exc:
        raise ValueError("hold minutes must be a positive integer") from exc
    if duration <= 0:
        raise ValueError("hold minutes must be a positive integer")
    return now + timedelta(minutes=duration)


def payment_hold_expiry(now: datetime, current_expiry: datetime, minutes: int) -> datetime:
    """Extend a live inventory hold for payment without ever shortening it."""
    candidate = hold_expiry(now, minutes)
    return max(current_expiry, candidate)


def amount_due_now(mode: str, total_minor: int, reservation_minor: int) -> int:
    normalized = (mode or "").strip().lower()
    total = max(int(total_minor), 0)
    reservation = max(int(reservation_minor), 0)
    if normalized == "book_now":
        return total
    if normalized == "reserve":
        if reservation <= 0:
            raise ValueError("reservation amount must be greater than zero")
        return min(reservation, total) if total else reservation
    raise ValueError("unsupported booking mode")


def booking_price_quote(
    amount_minor: int,
    security_deposit_minor: int,
    addon_amounts,
    booking_mode: str,
    reservation_amount_minor: int = 0,
) -> dict:
    """Return the canonical server-side price breakdown for a booking."""
    subtotal = max(int(amount_minor or 0), 0)
    security = max(int(security_deposit_minor or 0), 0)
    addon_total = sum(max(int(value or 0), 0) for value in (addon_amounts or []))
    total = subtotal + security + addon_total
    due_now = amount_due_now(booking_mode, total, reservation_amount_minor)
    return {
        "subtotal_minor": subtotal,
        "security_deposit_minor": security,
        "addon_total_minor": addon_total,
        "total_minor": total,
        "amount_due_now_minor": due_now,
    }


def transition_booking(current: str, event: str) -> str:
    key = ((current or "").strip().lower(), (event or "").strip().lower())
    try:
        return BOOKING_TRANSITIONS[key]
    except KeyError as exc:
        raise ValueError(f"illegal booking transition: {key[0]} + {key[1]}") from exc


def transition_hold(current: str, event: str) -> str:
    key = ((current or "").strip().lower(), (event or "").strip().lower())
    try:
        return HOLD_TRANSITIONS[key]
    except KeyError as exc:
        raise ValueError(f"illegal hold transition: {key[0]} + {key[1]}") from exc


def overlaps(start_a: date, end_a: date, start_b: date, end_b: date) -> bool:
    """Return True when half-open intervals [start,end) overlap."""
    return start_a < end_b and start_b < end_a


def hash_share_token(raw_token: str) -> str:
    import hashlib
    value = (raw_token or "").encode("utf-8")
    return hashlib.sha256(value).hexdigest()
