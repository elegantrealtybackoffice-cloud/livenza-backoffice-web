"""External provider adapters used by the Livenza.life consumer platform."""
from __future__ import annotations

import os
import uuid
import base64
from email.message import EmailMessage
import requests


_CASHFREE_TEST_ORDERS = {}


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


class CashfreeGateway:
    API_VERSION = "2025-01-01"

    def __init__(self, client_id: str, client_secret: str, environment: str = "sandbox", test_stub: bool = False):
        self.client_id=str(client_id or "").strip()
        self.client_secret=str(client_secret or "").strip()
        self.environment="production" if str(environment or "").strip().lower() in {"production","prod","live"} else "sandbox"
        self.test_stub=bool(test_stub)
        self.base_url="https://api.cashfree.com/pg" if self.environment=="production" else "https://sandbox.cashfree.com/pg"
        self._stub_orders=_CASHFREE_TEST_ORDERS

    @classmethod
    def from_env(cls):
        app_env=(os.getenv("LIVENZA_ENV") or os.getenv("FLASK_ENV") or "").strip().lower()
        cashfree_env=(os.getenv("CASHFREE_ENVIRONMENT") or ("production" if app_env=="production" else "sandbox")).strip().lower()
        test_stub=os.getenv("CASHFREE_TEST_STUB","0")=="1" and app_env in {"test","testing","development","dev","local"}
        return cls(os.getenv("CASHFREE_CLIENT_ID",""),os.getenv("CASHFREE_CLIENT_SECRET",""),environment=cashfree_env,test_stub=test_stub)

    def _headers(self, *, idempotency_key: str = "") -> dict:
        headers={"Content-Type":"application/json","Accept":"application/json","x-api-version":self.API_VERSION,"x-client-id":self.client_id,"x-client-secret":self.client_secret}
        if idempotency_key: headers["x-idempotency-key"]=idempotency_key
        return headers

    def create_order(self, amount_minor: int, currency: str, order_id: str, customer: dict, notes: dict, return_url: str, notify_url: str) -> dict:
        amount=int(amount_minor or 0)
        if amount < 100:
            raise ValueError("Cashfree order amount must be at least INR 1.00")
        order_id=str(order_id or "").strip()
        if not order_id:
            raise ValueError("Cashfree order id is required")
        customer=customer or {}
        phone=''.join(ch for ch in str(customer.get("phone") or "") if ch.isdigit())
        if phone.startswith("91") and len(phone)==12: phone=phone[2:]
        payload={
            "order_id":order_id,
            "order_amount":round(amount/100,2),
            "order_currency":str(currency or "INR"),
            "customer_details":{
                "customer_id":str(customer.get("id") or "")[:50] or f"guest_{uuid.uuid4().hex[:12]}",
                "customer_phone":phone[:10],
                "customer_name":str(customer.get("name") or "")[:100],
                "customer_email":str(customer.get("email") or "")[:100],
            },
            "order_meta":{"return_url":str(return_url or ""),"notify_url":str(notify_url or "")},
            "order_note":str((notes or {}).get("note") or "Livenza payment")[:180],
            "order_tags":{str(k)[:40]:str(v)[:120] for k,v in (notes or {}).items() if k!="note"},
        }
        if self.test_stub:
            result={"order_id":order_id,"cf_order_id":f"cf_test_{uuid.uuid4().hex[:16]}","order_status":"ACTIVE","order_amount":payload["order_amount"],"order_currency":payload["order_currency"],"payment_session_id":f"session_test_{uuid.uuid4().hex}"}
            self._stub_orders[order_id]=dict(result)
            return result
        if not (self.client_id and self.client_secret):
            raise RuntimeError("Cashfree is not configured")
        response=requests.post(f"{self.base_url}/orders",headers=self._headers(idempotency_key=str(uuid.uuid4())),json=payload,timeout=20)
        if not response.ok:
            raise RuntimeError("Cashfree order creation failed")
        body=response.json()
        if not body.get("order_id") or not body.get("payment_session_id"):
            raise RuntimeError("Cashfree order response is incomplete")
        return body

    def fetch_order(self, order_id: str) -> dict:
        order_id=str(order_id or "").strip()
        if self.test_stub:
            if order_id not in self._stub_orders: raise LookupError("Cashfree order not found")
            return dict(self._stub_orders[order_id])
        if not (self.client_id and self.client_secret):
            raise RuntimeError("Cashfree is not configured")
        response=requests.get(f"{self.base_url}/orders/{order_id}",headers=self._headers(),timeout=20)
        if not response.ok:
            raise RuntimeError("Cashfree order lookup failed")
        return response.json()

    def mark_test_order_paid(self, order_id: str) -> dict:
        """Mark a local Cashfree stub order paid; never available for real provider traffic."""
        if not self.test_stub:
            raise RuntimeError("Cashfree test order mutation is disabled")
        order_id=str(order_id or "").strip()
        if order_id not in self._stub_orders:
            raise LookupError("Cashfree order not found")
        self._stub_orders[order_id]=dict(self._stub_orders[order_id],order_status="PAID")
        return dict(self._stub_orders[order_id])


_RADIUS_TEST_STATE = {}


class RadiusAdapter:
    """Configuration-driven Radius/Xenius partner adapter.

    Radius partner endpoints are private, so live endpoint paths and auth are
    supplied through environment/config instead of being guessed in source.
    """
    def __init__(
        self, base_url: str, auth_token: str, *, enabled: bool = False,
        test_stub: bool = False, snapshot_path: str = "", recharge_path: str = "",
        status_path: str = "", auth_header: str = "Authorization", auth_scheme: str = "Bearer",
    ):
        self.base_url=str(base_url or "").strip().rstrip('/')
        self.auth_token=str(auth_token or "").strip()
        self.enabled=bool(enabled)
        self.test_stub=bool(test_stub)
        self.snapshot_path=str(snapshot_path or "").strip()
        self.recharge_path=str(recharge_path or "").strip()
        self.status_path=str(status_path or "").strip()
        self.auth_header=str(auth_header or "Authorization").strip() or "Authorization"
        self.auth_scheme=str(auth_scheme or "").strip()
        self._stub_state=_RADIUS_TEST_STATE

    @classmethod
    def from_env(cls):
        app_env=(os.getenv("LIVENZA_ENV") or os.getenv("FLASK_ENV") or "").strip().lower()
        test_stub=os.getenv("RADIUS_TEST_STUB","0")=="1" and app_env in {"test","testing","development","dev","local"}
        enabled=os.getenv("RADIUS_ENABLED","0")=="1" or test_stub
        return cls(
            os.getenv("RADIUS_BASE_URL",""), os.getenv("RADIUS_AUTH_TOKEN",""), enabled=enabled,
            test_stub=test_stub, snapshot_path=os.getenv("RADIUS_SNAPSHOT_PATH",""),
            recharge_path=os.getenv("RADIUS_RECHARGE_PATH",""), status_path=os.getenv("RADIUS_STATUS_PATH",""),
            auth_header=os.getenv("RADIUS_AUTH_HEADER","Authorization"), auth_scheme=os.getenv("RADIUS_AUTH_SCHEME","Bearer"),
        )

    def _configured(self, path: str) -> bool:
        return bool(self.enabled and self.base_url and self.auth_token and str(path or "").strip())

    def _headers(self, *, idempotency_key: str = "") -> dict:
        credential=f"{self.auth_scheme} {self.auth_token}".strip() if self.auth_scheme else self.auth_token
        headers={"Accept":"application/json","Content-Type":"application/json",self.auth_header:credential}
        if idempotency_key:
            headers["Idempotency-Key"]=str(idempotency_key)
        return headers

    @staticmethod
    def _path(template: str, *, account_id: str = "", meter_id: str = "", reference: str = "") -> str:
        from urllib.parse import quote
        return str(template or "").format(
            account_id=quote(str(account_id or ""),safe=""), meter_id=quote(str(meter_id or ""),safe=""),
            reference=quote(str(reference or ""),safe=""),
        )

    @staticmethod
    def _snapshot_payload(body: dict) -> dict:
        data=body if isinstance(body,dict) else {}
        balance=data.get("balance_minor")
        if balance is None and data.get("balance") is not None:
            try: balance=int(round(float(data.get("balance"))*100))
            except Exception: balance=None
        return {
            "available":True,
            "balance_minor":int(balance) if balance is not None else None,
            "currency":str(data.get("currency") or "INR"),
            "reading":str(data.get("reading") or data.get("meter_reading") or ""),
            "reading_unit":str(data.get("reading_unit") or data.get("unit") or "kWh"),
            "status":str(data.get("status") or "active"),
            "source_breakdown":data.get("source_breakdown") if isinstance(data.get("source_breakdown"),list) else [],
            "raw":data,
        }

    def get_snapshot(self, account_id: str, meter_id: str) -> dict:
        if self.test_stub:
            key=(str(account_id),str(meter_id))
            state=self._stub_state.setdefault(key,{"balance_minor":int(os.getenv("RADIUS_TEST_BALANCE_MINOR","50000") or 50000),"reading":"0","credits":{}})
            return {"available":True,"balance_minor":int(state["balance_minor"]),"currency":"INR","reading":str(state.get("reading") or "0"),"reading_unit":"kWh","status":"active","source_breakdown":[]}
        if not self._configured(self.snapshot_path):
            raise RuntimeError("Radius partner API is not configured")
        path=self._path(self.snapshot_path,account_id=account_id,meter_id=meter_id)
        response=requests.get(f"{self.base_url}{path}",headers=self._headers(),timeout=20)
        if not response.ok:
            raise RuntimeError("Radius meter snapshot request failed")
        return self._snapshot_payload(response.json())

    def credit_recharge(self, account_id: str, meter_id: str, amount_minor: int, currency: str, idempotency_key: str) -> dict:
        amount=int(amount_minor or 0)
        if amount <= 0:
            raise ValueError("Recharge amount must be positive")
        idem=str(idempotency_key or "").strip()
        if not idem:
            raise ValueError("Recharge idempotency key is required")
        if self.test_stub:
            key=(str(account_id),str(meter_id))
            state=self._stub_state.setdefault(key,{"balance_minor":int(os.getenv("RADIUS_TEST_BALANCE_MINOR","50000") or 50000),"reading":"0","credits":{}})
            if idem not in state["credits"]:
                state["balance_minor"]+=amount
                state["credits"][idem]={"provider_reference":f"radius_test_{uuid.uuid4().hex[:16]}","status":"credited"}
            return dict(state["credits"][idem])
        if not self._configured(self.recharge_path):
            raise RuntimeError("Radius partner API is not configured")
        path=self._path(self.recharge_path,account_id=account_id,meter_id=meter_id)
        payload={"account_id":str(account_id),"meter_id":str(meter_id),"amount_minor":amount,"currency":str(currency or "INR")}
        response=requests.post(f"{self.base_url}{path}",headers=self._headers(idempotency_key=idem),json=payload,timeout=25)
        if not response.ok:
            raise RuntimeError("Radius meter recharge request failed")
        body=response.json()
        reference=str((body or {}).get("provider_reference") or (body or {}).get("transaction_id") or (body or {}).get("reference") or "")
        status=str((body or {}).get("status") or "processing").strip().lower()
        if not reference:
            raise RuntimeError("Radius recharge response is incomplete")
        return {"provider_reference":reference,"status":status,"raw":body}

    def get_recharge_status(self, reference: str) -> dict:
        if self.test_stub:
            for state in self._stub_state.values():
                for result in state.get("credits",{}).values():
                    if result.get("provider_reference")==reference:
                        return dict(result)
            raise LookupError("Radius recharge not found")
        if not self._configured(self.status_path):
            raise RuntimeError("Radius recharge status API is not configured")
        path=self._path(self.status_path,reference=reference)
        response=requests.get(f"{self.base_url}{path}",headers=self._headers(),timeout=20)
        if not response.ok:
            raise RuntimeError("Radius recharge status request failed")
        body=response.json()
        return {"provider_reference":str(body.get("provider_reference") or body.get("transaction_id") or reference),"status":str(body.get("status") or "processing").lower(),"raw":body}


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
