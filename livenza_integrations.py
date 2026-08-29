"""External provider adapters used by the Livenza.life consumer platform."""
from __future__ import annotations

import os
import uuid
import base64
from email.message import EmailMessage
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



def send_whatsapp_text(config: dict, destination: str, subject: str, body: str) -> dict:
    """Send a transactional text message using the configured WhatsApp Cloud connection."""
    cfg=config or {}; token=str(cfg.get('token') or '').strip(); phone_id=str(cfg.get('phone_number_id') or '').strip()
    version=str(cfg.get('graph_version') or 'v23.0').strip() or 'v23.0'
    to=''.join(ch for ch in str(destination or '') if ch.isdigit())
    if not (token and phone_id and to):
        return {'accepted':False,'provider':'whatsapp_cloud','error_code':'integration_not_configured'}
    try:
        response=requests.post(
            f'https://graph.facebook.com/{version}/{phone_id}/messages',
            headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},
            json={'messaging_product':'whatsapp','to':to,'type':'text','text':{'body':str(body or '')[:4096],'preview_url':False}},
            timeout=25,
        )
        if not response.ok:
            return {'accepted':False,'provider':'whatsapp_cloud','error_code':f'http_{response.status_code}'}
        try: reference=str((response.json().get('messages') or [{}])[0].get('id') or '')
        except Exception: reference=''
        return {'accepted':True,'provider':'whatsapp_cloud','reference':reference}
    except Exception:
        return {'accepted':False,'provider':'whatsapp_cloud','error_code':'provider_exception'}


def send_google_email_text(access_token: str, destination: str, subject: str, body: str) -> dict:
    """Send transactional plain text through the existing connected Google account."""
    token=str(access_token or '').strip(); recipient=str(destination or '').strip()
    if not (token and recipient):
        return {'accepted':False,'provider':'google_email','error_code':'integration_not_configured'}
    try:
        mail=EmailMessage(); mail['To']=recipient; mail['Subject']=str(subject or 'Livenza update')[:240]
        mail.set_content(str(body or ''))
        raw=base64.urlsafe_b64encode(mail.as_bytes()).decode('ascii').rstrip('=')
        response=requests.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},
            json={'raw':raw},timeout=25,
        )
        if not response.ok:
            return {'accepted':False,'provider':'google_email','error_code':f'http_{response.status_code}'}
        try: reference=str(response.json().get('id') or '')
        except Exception: reference=''
        return {'accepted':True,'provider':'google_email','reference':reference}
    except Exception:
        return {'accepted':False,'provider':'google_email','error_code':'provider_exception'}
