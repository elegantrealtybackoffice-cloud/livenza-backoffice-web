"""Receipt metadata and printable HTML rendering for Livenza.life V1."""
from __future__ import annotations

import hashlib
import html


def receipt_number(booking_id: str, payment_id: str) -> str:
    digest = hashlib.sha256(f"{booking_id}|{payment_id}".encode("utf-8")).hexdigest()[:12].upper()
    return f"LVZ-R-{digest}"


def build_receipt_view(*, booking_id: str, payment_id: str, property_name: str,
                       amount_minor: int, currency: str, paid_at: str) -> dict:
    return {
        "receipt_number": receipt_number(booking_id, payment_id),
        "booking_id": booking_id,
        "payment_id": payment_id,
        "property_name": property_name,
        "amount_minor": int(amount_minor),
        "currency": currency or "INR",
        "paid_at": paid_at,
    }


def render_receipt_html(view: dict) -> str:
    amount = int(view.get("amount_minor") or 0) / 100
    currency = html.escape(str(view.get("currency") or "INR"))
    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{html.escape(str(view.get('receipt_number') or 'Livenza Receipt'))}</title>
<style>body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#f6f6f4;color:#111}}main{{max-width:720px;margin:40px auto;background:white;padding:40px;border-radius:20px}}h1{{font-size:32px}}dl{{display:grid;grid-template-columns:180px 1fr;gap:12px}}dt{{color:#666}}dd{{margin:0;font-weight:650}}@media print{{body{{background:white}}main{{margin:0;max-width:none;border-radius:0}}button{{display:none}}}}</style></head><body><main><p>LIVENZA.LIFE</p><h1>Payment receipt</h1><dl>
<dt>Receipt</dt><dd>{html.escape(str(view.get('receipt_number') or ''))}</dd>
<dt>Booking</dt><dd>{html.escape(str(view.get('booking_id') or ''))}</dd>
<dt>Payment</dt><dd>{html.escape(str(view.get('payment_id') or ''))}</dd>
<dt>Property</dt><dd>{html.escape(str(view.get('property_name') or 'Livenza stay'))}</dd>
<dt>Amount</dt><dd>{currency} {amount:,.2f}</dd>
<dt>Paid at</dt><dd>{html.escape(str(view.get('paid_at') or ''))}</dd></dl><p><button onclick=\"window.print()\">Print receipt</button></p></main></body></html>"""
