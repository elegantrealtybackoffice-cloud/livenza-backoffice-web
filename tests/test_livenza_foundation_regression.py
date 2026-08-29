from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
APP_SOURCE = APP_PATH.read_text(encoding="utf-8")
TREE = ast.parse(APP_SOURCE)
CLASS_NAMES = {node.name for node in TREE.body if isinstance(node, ast.ClassDef)}

LEGACY_MODULES = {
    "agreements", "rooms", "reviews", "food", "rentok", "banking",
    "electricity", "queries", "video_wall", "whatsapp", "email", "drive",
    "integrations", "letterhead",
}


def _literal_assignment(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"assignment {name} not found")


def test_legacy_operational_models_remain_defined():
    for name in ["User", "Room", "Tenant", "IntegrationProvider", "VaultSecret", "AuditEvent"]:
        assert name in CLASS_NAMES


def test_existing_module_registry_keys_are_preserved():
    modules = _literal_assignment("MODULES")
    assert LEGACY_MODULES.issubset(set(modules))


def test_can_access_still_uses_existing_permission_resolution():
    start = APP_SOURCE.index("def can_access(module, user=None):")
    fragment = APP_SOURCE[start:start + 300]
    assert "module not in MODULES" in fragment
    assert "module in user_permissions(user)" in fragment


def test_consumer_api_registration_does_not_replace_staff_authentication():
    assert "def register_livenza_consumer_api():" in APP_SOURCE
    assert "def login" in APP_SOURCE
    assert "password_hash" in APP_SOURCE
    assert "livenza_customer_session" not in APP_SOURCE.split("def login", 1)[1].split("def ", 1)[0]
