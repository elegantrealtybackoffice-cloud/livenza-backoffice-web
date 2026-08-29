"""Pure payment helpers for Livenza.life V1."""
from __future__ import annotations

import hashlib
import hmac


def verify_razorpay_webhook(raw_body: bytes, signature: str, secret: str) -> bool:
    if not isinstance(raw_body, (bytes, bytearray)):
        return False
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), bytes(raw_body), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def payment_event_state(event_type: str):
    event = (event_type or "").strip().lower()
    if event in {"payment.captured", "order.paid"}:
        return "paid"
    if event == "payment.failed":
        return "failed"
    if event in {"payment.authorized", "order.attempted"}:
        return "pending"
    return None


def public_gateway_config(config: dict) -> dict:
    return {"key_id": str((config or {}).get("key_id") or "")}
