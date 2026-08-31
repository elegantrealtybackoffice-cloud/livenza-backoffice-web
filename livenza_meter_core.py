"""Pure helpers for Livenza tenant prepaid-meter and recharge flows."""
from __future__ import annotations

ACTIVE_RECHARGE_STATES={"payment_pending","paid","radius_processing","review_required"}
FINAL_RECHARGE_STATES={"recharged","refund_followup","cancelled"}


def normalize_recharge_amount(amount_minor, minimum_minor=1000, maximum_minor=5000000):
    amount=int(amount_minor or 0)
    if amount < int(minimum_minor):
        raise ValueError("Recharge amount is below the minimum allowed amount.")
    if amount > int(maximum_minor):
        raise ValueError("Recharge amount is above the maximum allowed amount.")
    return amount


def recharge_can_start(existing_statuses):
    return not any(str(status or "").strip().lower() in ACTIVE_RECHARGE_STATES for status in (existing_statuses or []))


def masked_meter_label(value):
    raw=str(value or "").strip()
    if not raw:
        return "Meter"
    return f"Meter ••••{raw[-4:]}" if len(raw)>4 else f"Meter ••••{raw}"
