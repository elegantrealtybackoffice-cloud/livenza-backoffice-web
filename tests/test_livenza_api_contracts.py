from pathlib import Path
from types import SimpleNamespace
import livenza_api_v1

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / "livenza_api_v1.py").read_text(encoding="utf-8")
MIGRATION = (ROOT / "migrations/livenza_v1_foundation.sql").read_text(encoding="utf-8")
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")

SENSITIVE_KEYS = {
    "otp_hash", "token_hash", "password_hash", "ciphertext", "nonce", "permissions_json",
}


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in SENSITIVE_KEYS
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)


def test_public_serializers_have_no_sensitive_keys():
    customer = SimpleNamespace(
        public_id="c1", full_name="Resident", primary_mobile="+919876543210",
        primary_email="r@example.com", status="active", otp_hash="x", token_hash="x",
    )
    prop = SimpleNamespace(
        id=1, slug="p1", name="P1", city="Jaipur", area="Sitapura",
        summary="Home", stay_types=["student"], ciphertext="x",
    )
    walk(livenza_api_v1._serialize_customer(customer))
    walk(livenza_api_v1.serialize_property(prop))


def test_otp_and_session_secrets_are_hash_only_in_persistence_models():
    assert "otp_hash = db.Column" in APP_SOURCE
    assert "token_hash = db.Column" in APP_SOURCE
    assert "otp = db.Column" not in APP_SOURCE
    assert "session_token = db.Column" not in APP_SOURCE


def test_migration_is_additive_and_does_not_mutate_legacy_tables():
    upper = MIGRATION.upper()
    assert "DROP TABLE" not in upper
    assert "DROP COLUMN" not in upper
    assert "RENAME TABLE" not in upper
    assert "ALTER TABLE USER" not in upper
    assert "ALTER TABLE ROOM" not in upper
    assert "ALTER TABLE TENANT" not in upper


def test_test_otp_is_not_enabled_by_flag_alone(monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    monkeypatch.delenv("LIVENZA_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert livenza_api_v1._test_mode_enabled() is False


def test_api_source_never_serializes_hash_or_vault_fields():
    serializer_section = API_SOURCE.split("def _serialize_customer", 1)[1].split("def serialize_property", 1)[0]
    property_section = API_SOURCE.split("def serialize_property", 1)[1].split("def register_api_v1", 1)[0]
    for forbidden in SENSITIVE_KEYS:
        assert f'"{forbidden}"' not in serializer_section
        assert f'"{forbidden}"' not in property_section
