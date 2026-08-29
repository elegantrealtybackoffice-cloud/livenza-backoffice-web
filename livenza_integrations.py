"""External provider adapters used by the Livenza.life consumer platform."""
from __future__ import annotations

import os
import uuid
import requests


class RazorpayGateway:
    def __init__(self, key_id: str, key_secret: str, webhook_secret: str = "", test_stub: bool = False):
        self.key_id = key_id or ""
        self.key_secret = key_secret or ""
        self.webhook_secret = webhook_secret or ""
        self.test_stub = bool(test_stub)

    @classmethod
    def from_env(cls):
        env = (os.getenv("LIVENZA_ENV") or os.getenv("FLASK_ENV") or "").strip().lower()
        test_stub = os.getenv("RAZORPAY_TEST_STUB", "0") == "1" and env in {"test", "testing", "development", "dev", "local"}
        return cls(
            os.getenv("RAZORPAY_KEY_ID", ""),
            os.getenv("RAZORPAY_KEY_SECRET", ""),
            os.getenv("RAZORPAY_WEBHOOK_SECRET", ""),
            test_stub=test_stub,
        )

    def create_order(self, amount_minor: int, currency: str, receipt: str, notes: dict) -> dict:
        amount = int(amount_minor)
        if amount <= 0:
            raise ValueError("payment amount must be positive")
        if self.test_stub:
            return {
                "id": f"order_test_{uuid.uuid4().hex[:18]}",
                "amount": amount,
                "currency": currency or "INR",
                "receipt": receipt,
                "status": "created",
            }
        if not (self.key_id and self.key_secret):
            raise RuntimeError("Razorpay is not configured")
        response = requests.post(
            "https://api.razorpay.com/v1/orders",
            auth=(self.key_id, self.key_secret),
            json={"amount": amount, "currency": currency or "INR", "receipt": receipt, "notes": notes or {}},
            timeout=20,
        )
        if not response.ok:
            raise RuntimeError("Razorpay order creation failed")
        body = response.json()
        if not body.get("id"):
            raise RuntimeError("Razorpay order response is missing order id")
        return body
