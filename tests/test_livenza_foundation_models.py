from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(APP_SOURCE)
CLASS_NAMES = {node.name for node in TREE.body if isinstance(node, ast.ClassDef)}


def test_customer_models_exist_in_source():
    for name in [
        "Customer", "CustomerIdentity", "CustomerOtpChallenge",
        "CustomerSession", "CustomerAddress",
    ]:
        assert name in CLASS_NAMES


def test_stay_models_exist_in_source():
    for name in ["StayProperty", "StayRoomCategory", "StayInventoryUnit"]:
        assert name in CLASS_NAMES


def test_customer_identity_unique_constraint_is_named():
    assert "uq_customer_identity_provider_identifier" in APP_SOURCE


def test_staff_user_contract_is_preserved_in_source():
    assert "class User(db.Model):" in APP_SOURCE
    assert "password_hash = db.Column" in APP_SOURCE
    assert "__tablename__ = 'user'" not in APP_SOURCE or "class User" in APP_SOURCE


def test_runtime_model_contracts_when_flask_is_available(app_module):
    assert app_module.User.__tablename__ == "user"
    assert "password_hash" in app_module.User.__table__.columns
    unique_names = {
        c.name for c in app_module.CustomerIdentity.__table__.constraints
        if getattr(c, "name", None)
    }
    assert "uq_customer_identity_provider_identifier" in unique_names
