from pathlib import Path
from types import SimpleNamespace

import livenza_api_v1

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / "livenza_api_v1.py").read_text(encoding="utf-8")
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def test_api_module_uses_versioned_prefix_and_expected_auth_routes():
    assert 'url_prefix="/api/v1"' in API_SOURCE
    for route in [
        '/auth/otp/request', '/auth/otp/verify', '/auth/logout', '/me',
    ]:
        assert route in API_SOURCE


def test_customer_session_cookie_contract_is_secure_by_configuration():
    assert 'COOKIE_NAME = "livenza_customer_session"' in API_SOURCE
    assert 'httponly=True' in API_SOURCE
    assert 'secure=bool(app.config.get("SESSION_COOKIE_SECURE", False))' in API_SOURCE
    assert 'samesite="Lax"' in API_SOURCE


def test_test_otp_requires_explicit_nonproduction_environment(monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    monkeypatch.setenv("FLASK_ENV", "production")
    assert livenza_api_v1._test_mode_enabled() is False
    monkeypatch.setenv("FLASK_ENV", "test")
    assert livenza_api_v1._test_mode_enabled() is True


def test_customer_serializer_exposes_only_public_fields():
    row = SimpleNamespace(
        public_id="customer-public-id",
        full_name="Resident",
        primary_mobile="+919876543210",
        primary_email="resident@example.com",
        status="active",
        otp_hash="must-not-leak",
        token_hash="must-not-leak",
    )
    payload = livenza_api_v1._serialize_customer(row)
    assert payload == {
        "id": "customer-public-id",
        "full_name": "Resident",
        "primary_mobile": "+919876543210",
        "primary_email": "resident@example.com",
        "status": "active",
    }


def test_otp_adapter_reuses_integration_center_backed_whatsapp_config():
    assert "def send_customer_otp(identifier, otp):" in APP_SOURCE
    assert "_letterhead_whatsapp_config()" in APP_SOURCE
    adapter = APP_SOURCE.split("def send_customer_otp(identifier, otp):", 1)[1].split("def register_livenza_consumer_api", 1)[0]
    assert "WHATSAPP_CLOUD_TOKEN" not in adapter
    assert "WHATSAPP_PHONE_NUMBER_ID" not in adapter


def test_runtime_otp_request_and_verify_when_flask_is_available(client, clean_customer_tables, monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    monkeypatch.setenv("FLASK_ENV", "test")
    request_res = client.post("/api/v1/auth/otp/request", json={"mobile": "9876543210"})
    assert request_res.status_code == 202
    otp = request_res.get_json()["test_otp"]
    verify = client.post("/api/v1/auth/otp/verify", json={"mobile": "9876543210", "otp": otp})
    assert verify.status_code == 200
    cookie = verify.headers.get("Set-Cookie", "")
    assert "livenza_customer_session=" in cookie
    assert "HttpOnly" in cookie
    me = client.get("/api/v1/me")
    assert me.status_code == 200
    assert me.get_json()["customer"]["primary_mobile"] == "+919876543210"


def test_runtime_wrong_otp_is_rejected_when_flask_is_available(client, clean_customer_tables, monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    monkeypatch.setenv("FLASK_ENV", "test")
    client.post("/api/v1/auth/otp/request", json={"mobile": "9876543211"})
    res = client.post("/api/v1/auth/otp/verify", json={"mobile": "9876543211", "otp": "000000"})
    assert res.status_code == 401


def test_runtime_otp_rate_limit_when_flask_is_available(client, clean_customer_tables, monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    monkeypatch.setenv("FLASK_ENV", "test")
    monkeypatch.setenv("CUSTOMER_OTP_MAX_REQUESTS_15M", "5")
    for _ in range(5):
        res = client.post("/api/v1/auth/otp/request", json={"mobile": "9876543299"})
        assert res.status_code == 202
    blocked = client.post("/api/v1/auth/otp/request", json={"mobile": "9876543299"})
    assert blocked.status_code == 429


def test_runtime_staff_password_login_still_redirects_when_flask_is_available(client):
    res = client.post(
        "/login",
        data={"username": "admin", "auth_method": "password", "password": "TestOnlyAdminPassword!123"},
        follow_redirects=False,
    )
    assert res.status_code in {302, 303}
