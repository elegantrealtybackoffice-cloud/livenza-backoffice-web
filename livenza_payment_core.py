"""Pure payment helpers for Livenza.life V1."""
from __future__ import annotations

import base64
import hashlib
import hmac

SUPPORTED_PAYMENT_SOURCES = {'booking', 'store_order', 'tenant_due', 'meter_recharge'}


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


def verify_cashfree_webhook(raw_body: bytes, signature: str, timestamp: str, secret: str) -> bool:
    if not isinstance(raw_body,(bytes,bytearray)) or not signature or not timestamp or not secret:
        return False
    message=str(timestamp).encode("utf-8")+bytes(raw_body)
    expected=base64.b64encode(hmac.new(secret.encode("utf-8"),message,hashlib.sha256).digest()).decode("ascii")
    return hmac.compare_digest(expected,str(signature))


def cashfree_payment_event_state(event_type: str):
    event=str(event_type or "").strip().upper()
    if event == "PAYMENT_SUCCESS_WEBHOOK":
        return "paid"
    if event in {"PAYMENT_FAILED_WEBHOOK","PAYMENT_USER_DROPPED_WEBHOOK"}:
        return "failed"
    return None
