import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask, redirect, url_for
from werkzeug.test import Client
from werkzeug.security import generate_password_hash
from werkzeug.wrappers import Response


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FORCE_HTTPS"] = "0"
os.environ["LIVENZA_ENV"] = "testing"
os.environ["CUSTOMER_AUTH_TEST_MODE"] = "1"
os.environ["LIVENZA_CONSUMER_PLATFORM_ENABLED"] = "1"

from livenza_staff_auth import mount_backoffice, normalize_backoffice_next
from app import (
    Setting,
    User,
    WebAuthnCredential,
    app,
    db,
    send_customer_otp,
    set_setting,
)


class BackofficeNextTests(unittest.TestCase):
    def test_accepts_only_local_backoffice_destinations(self):
        self.assertEqual(normalize_backoffice_next("/backoffice"), "/backoffice")
        self.assertEqual(
            normalize_backoffice_next("/backoffice/rooms?tab=available#ignored"),
            "/backoffice/rooms?tab=available",
        )

    def test_rejects_external_encoded_and_lookalike_destinations(self):
        for value in (
            "https://evil.example/backoffice",
            "//evil.example/backoffice",
            "%2F%2Fevil.example/backoffice",
            "/backoffice-evil",
            "/my",
            "/backoffice/../my",
            "/backoffice/%2e%2e/my",
            "/backoffice/%252e%252e/my",
            "/backoffice\\@evil.example",
            "",
            None,
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize_backoffice_next(value), "/backoffice")


class BackofficeMountTests(unittest.TestCase):
    def test_mounted_app_preserves_prefix_in_generated_urls(self):
        mounted = Flask("mounted-test")

        @mounted.get("/")
        def home():
            return redirect(url_for("login"))

        @mounted.get("/login")
        def login():
            return "login"

        client = Client(mount_backoffice(mounted.wsgi_app), Response)
        response = client.get("/backoffice/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/backoffice/login")
        self.assertEqual(client.get("/login").status_code, 200)


class CustomerOtpDeliveryTests(unittest.TestCase):
    def test_production_otp_uses_configured_whatsapp_authentication_template(self):
        config = {
            "token": "cloud-token",
            "phone_number_id": "phone-number-id",
            "graph_version": "v23.0",
        }
        accepted = SimpleNamespace(ok=True)
        environment = {
            "LIVENZA_ENV": "production",
            "CUSTOMER_AUTH_TEST_MODE": "0",
            "WHATSAPP_OTP_TEMPLATE_NAME": "livenza_login_otp",
            "WHATSAPP_OTP_TEMPLATE_LANGUAGE": "en_US",
        }

        with patch.dict(os.environ, environment, clear=True):
            with patch("app._letterhead_whatsapp_config", return_value=config):
                with patch("app.requests.post", return_value=accepted) as request_post:
                    result = send_customer_otp("+919876543210", "123456")

        self.assertEqual(result, {"accepted": True, "provider": "whatsapp_cloud"})
        self.assertEqual(
            request_post.call_args.kwargs["json"],
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": "919876543210",
                "type": "template",
                "template": {
                    "name": "livenza_login_otp",
                    "language": {"code": "en_US"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": "123456"}],
                        },
                        {
                            "type": "button",
                            "sub_type": "url",
                            "index": "0",
                            "parameters": [{"type": "text", "text": "123456"}],
                        },
                    ],
                },
            },
        )

    def test_production_otp_fails_before_delivery_without_template_configuration(self):
        config = {
            "token": "cloud-token",
            "phone_number_id": "phone-number-id",
            "graph_version": "v23.0",
        }
        environment = {
            "LIVENZA_ENV": "production",
            "CUSTOMER_AUTH_TEST_MODE": "0",
        }

        with patch.dict(os.environ, environment, clear=True):
            with patch("app._letterhead_whatsapp_config", return_value=config):
                with patch("app.requests.post") as request_post:
                    with self.assertRaisesRegex(
                        RuntimeError, "customer OTP delivery is not configured"
                    ):
                        send_customer_otp("+919876543210", "123456")

        request_post.assert_not_called()


class StaffBridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = app.test_client()
        with app.app_context():
            db.session.query(WebAuthnCredential).delete()
            db.session.query(User).delete()
            db.session.add_all(
                [
                    User(
                        username="manager",
                        password_hash=generate_password_hash("CorrectHorse!27"),
                        pattern_hash=generate_password_hash("pattern:0-1-2-5-8"),
                        role="manager",
                        permissions_json='["rooms"]',
                        active=True,
                    ),
                    User(
                        username="inactive",
                        password_hash=generate_password_hash("CorrectHorse!27"),
                        role="admin",
                        active=False,
                    ),
                    User(
                        username="admin",
                        password_hash=generate_password_hash("CorrectHorse!27"),
                        role="admin",
                        active=True,
                    ),
                ]
            )
            db.session.commit()
            set_setting("kiosk_mode_enabled", "0")

    def tearDown(self):
        with app.app_context():
            set_setting("kiosk_mode_enabled", "0")

    def test_password_bridge_sets_existing_uid_and_safe_redirect(self):
        response = self.client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
                "next": "/backoffice/rooms?tab=available",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["redirect"],
            "/backoffice/rooms?tab=available",
        )
        with self.client.session_transaction() as flask_session:
            self.assertIsInstance(flask_session.get("uid"), int)
            self.assertIn("kiosk_unlocked", flask_session)

    def test_invalid_or_inactive_account_never_sets_uid(self):
        attempts = (
            {"username": "manager", "method": "password", "credential": "wrong"},
            {
                "username": "inactive",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        for payload in attempts:
            with self.subTest(payload=payload):
                self.client.get("/logout")
                response = self.client.post("/api/staff/authenticate", json=payload)
                self.assertIn(response.status_code, (401, 403))
                with self.client.session_transaction() as flask_session:
                    self.assertNotIn("uid", flask_session)

    def test_pattern_bridge_uses_existing_pattern_hash(self):
        response = self.client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "pattern",
                "credential": "0-1-2-5-8",
            },
        )
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as flask_session:
            self.assertIsNotNone(flask_session.get("uid"))

    def test_staff_session_summary_exposes_no_permissions_or_credentials(self):
        self.client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        payload = self.client.get("/api/staff/session").get_json()
        self.assertEqual(payload["staff"]["role"], "manager")
        self.assertNotIn("permissions_json", str(payload))
        self.assertNotIn("password", str(payload).lower())

    def test_customer_otp_session_survives_staff_login(self):
        requested = self.client.post(
            "/api/v1/auth/otp/request",
            json={"mobile": "+919876543210"},
        )
        self.assertEqual(requested.status_code, 202)
        verified = self.client.post(
            "/api/v1/auth/otp/verify",
            json={
                "mobile": "+919876543210",
                "otp": requested.get_json()["test_otp"],
            },
        )
        self.assertEqual(verified.status_code, 200)
        response = self.client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        customer_cookie_headers = [
            value
            for value in response.headers.getlist("Set-Cookie")
            if value.startswith("livenza_customer_session=")
        ]
        self.assertEqual(customer_cookie_headers, [])
        self.assertEqual(self.client.get("/api/v1/me").status_code, 200)
        with self.client.session_transaction() as flask_session:
            self.assertIsNotNone(flask_session.get("uid"))

    def test_customer_logout_does_not_clear_staff_session(self):
        self.client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        requested = self.client.post(
            "/api/v1/auth/otp/request",
            json={"mobile": "+919876543210"},
        )
        self.client.post(
            "/api/v1/auth/otp/verify",
            json={
                "mobile": "+919876543210",
                "otp": requested.get_json()["test_otp"],
            },
        )
        self.assertEqual(self.client.post("/api/v1/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/me").status_code, 401)
        with self.client.session_transaction() as flask_session:
            self.assertIsNotNone(flask_session.get("uid"))

    def test_backoffice_mount_redirects_anonymous_user_to_public_staff_login(self):
        client = Client(app.wsgi_app, Response)
        response = client.get("/backoffice/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/backoffice/login", response.headers["Location"])
        bridge = client.get(response.headers["Location"])
        self.assertEqual(bridge.status_code, 302)
        self.assertTrue(
            bridge.headers["Location"].startswith(
                "/staff-login?next=%2Fbackoffice"
            )
        )

    def test_mounted_login_post_cannot_use_legacy_external_next(self):
        client = Client(app.wsgi_app, Response, use_cookies=True)
        response = client.post(
            "/backoffice/login?next=https://evil.example",
            data={
                "username": "manager",
                "auth_method": "password",
                "password": "CorrectHorse!27",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/staff-login?next=%2Fbackoffice")
        protected = client.get("/backoffice/rooms")
        self.assertEqual(protected.status_code, 302)
        self.assertTrue(protected.headers["Location"].startswith("/backoffice/login"))

    def test_real_mount_serves_authenticated_routes_assets_and_prefixed_client_paths(self):
        client = Client(app.wsgi_app, Response, use_cookies=True)
        client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        dashboard = client.get("/backoffice/")
        self.assertEqual(dashboard.status_code, 200)
        body = dashboard.get_data(as_text=True)
        self.assertIn('data-script-root="/backoffice"', body)
        self.assertIn('/backoffice/static/', body)

        rooms = client.get("/backoffice/rooms")
        self.assertEqual(rooms.status_code, 200)
        app_javascript = client.get("/backoffice/static/app.js")
        self.assertEqual(app_javascript.status_code, 200)
        script = app_javascript.get_data(as_text=True)
        app_javascript.close()
        self.assertIn("livenzaBackofficePath('/agreements/aadhaar-extract')", script)
        self.assertIn("livenzaBackofficePath('/video-wall#available-media')", script)
        self.assertIn("livenzaBackofficePath('/date-calculator')", script)
        self.assertIn("livenzaBackofficePath('/static/livenza_360_lifestyle_bg.jpg')", script)

    def test_real_mount_preserves_admin_and_manager_permissions(self):
        client = Client(app.wsgi_app, Response, use_cookies=True)
        client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        self.assertEqual(client.get("/backoffice/admin").status_code, 403)
        client.get("/backoffice/logout")
        client.post(
            "/api/staff/authenticate",
            json={
                "username": "admin",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        admin = client.get("/backoffice/admin")
        self.assertEqual(admin.status_code, 302)
        self.assertTrue(admin.headers["Location"].startswith("/backoffice/settings"))
        self.assertEqual(client.get(admin.headers["Location"]).status_code, 200)

    def test_kiosk_gate_redirects_prefixed_routes_inside_backoffice(self):
        with app.app_context():
            set_setting("kiosk_mode_enabled", "1")
        client = Client(app.wsgi_app, Response, use_cookies=True)
        authenticated = client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        self.assertEqual(authenticated.get_json()["redirect"], "/backoffice/kiosk")
        gated = client.get("/backoffice/rooms")
        self.assertEqual(gated.status_code, 302)
        self.assertTrue(gated.headers["Location"].startswith("/backoffice/kiosk"))

    def test_prefixed_permission_denial_stays_inside_backoffice(self):
        client = Client(app.wsgi_app, Response, use_cookies=True)
        client.post(
            "/api/staff/authenticate",
            json={
                "username": "manager",
                "method": "password",
                "credential": "CorrectHorse!27",
            },
        )
        response = client.get("/backoffice/admin")
        self.assertIn(response.status_code, (302, 403))
        if response.status_code == 302:
            self.assertTrue(response.headers["Location"].startswith("/backoffice"))

    def test_webauthn_redirect_preserves_legacy_root_and_safe_backoffice(self):
        from app import _webauthn_success_redirect

        self.assertEqual(_webauthn_success_redirect(None, True), "/")
        self.assertEqual(
            _webauthn_success_redirect("/backoffice/rooms", True),
            "/backoffice/rooms",
        )
        self.assertEqual(
            _webauthn_success_redirect("https://evil.example", True),
            "/backoffice",
        )
        self.assertEqual(
            _webauthn_success_redirect("/backoffice/rooms", False),
            "/backoffice/kiosk",
        )

    def test_webauthn_options_reject_an_rp_bound_to_the_old_subdomain(self):
        with app.app_context():
            user = User.query.filter_by(username="manager").one()
            user.webauthn_enabled = True
            db.session.add(
                WebAuthnCredential(
                    user_id=user.id,
                    credential_id=b"old-host-credential",
                    public_key=b"test-public-key",
                )
            )
            db.session.commit()
        with patch.dict(
            os.environ,
            {
                "WEBAUTHN_RP_ID": "backoffice.livenza.life",
                "WEBAUTHN_ORIGIN": "https://backoffice.livenza.life",
            },
            clear=False,
        ):
            response = self.client.post(
                "/api/webauthn/auth/options",
                json={"username": "manager", "next": "/backoffice"},
                base_url="https://livenza.life",
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn("different Livenza host", response.get_json()["error"])

    def test_webauthn_verifier_accepts_configured_unified_and_legacy_origins(self):
        from app import _webauthn_context

        with app.app_context():
            user = User.query.filter_by(username="manager").one()
            user.webauthn_enabled = True
            db.session.add(
                WebAuthnCredential(
                    user_id=user.id,
                    credential_id=b"\x01",
                    public_key=b"test-public-key",
                    sign_count=3,
                )
            )
            db.session.commit()
            user_id = user.id

        configured = {
            "WEBAUTHN_RP_ID": "livenza.life",
            "WEBAUTHN_ORIGIN": "https://livenza.life",
            "WEBAUTHN_ALLOWED_ORIGINS": "https://backoffice.livenza.life",
        }
        with patch.dict(os.environ, configured, clear=False):
            with app.test_request_context("/", base_url="https://livenza.life"):
                self.assertEqual(
                    _webauthn_context(),
                    (
                        "livenza.life",
                        ["https://livenza.life", "https://backoffice.livenza.life"],
                    ),
                )
            with self.client.session_transaction(base_url="https://livenza.life") as flask_session:
                flask_session["webauthn_auth_challenge"] = "dGVzdC1jaGFsbGVuZ2U="
                flask_session["webauthn_auth_user"] = user_id
                flask_session["webauthn_auth_next"] = "/backoffice/rooms"
            with patch(
                "webauthn.verify_authentication_response",
                return_value=SimpleNamespace(new_sign_count=4),
            ) as verify:
                response = self.client.post(
                    "/api/webauthn/auth/verify",
                    json={
                        "id": "AQ",
                        "rawId": "AQ",
                        "type": "public-key",
                        "response": {
                            "clientDataJSON": "AQ",
                            "authenticatorData": "AQ",
                            "signature": "AQ",
                            "userHandle": None,
                        },
                    },
                    base_url="https://livenza.life",
                )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.get_json()["redirect"], "/backoffice/rooms")
        self.assertEqual(
            verify.call_args.kwargs["expected_origin"],
            ["https://livenza.life", "https://backoffice.livenza.life"],
        )


if __name__ == "__main__":
    unittest.main()
