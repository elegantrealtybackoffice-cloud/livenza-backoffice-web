import importlib
import importlib.util
import os
import sys
import pytest


def _runtime_dependencies_available():
    required = ["flask", "flask_sqlalchemy", "sqlalchemy"]
    return all(importlib.util.find_spec(name) is not None for name in required)


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    if not _runtime_dependencies_available():
        pytest.skip("Flask runtime dependencies are not installed in this sandbox")
    db_path = tmp_path_factory.mktemp("livenza") / "foundation.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["FORCE_HTTPS"] = "0"
    os.environ["FLASK_ENV"] = "test"
    os.environ["CUSTOMER_AUTH_TEST_MODE"] = "1"
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("ADMIN_PASSWORD", "TestOnlyAdminPassword!123")
    sys.modules.pop("app", None)
    return importlib.import_module("app")


@pytest.fixture
def client(app_module):
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as client:
        yield client


@pytest.fixture
def clean_customer_tables(app_module):
    models = [
        app_module.CustomerSession,
        app_module.CustomerOtpChallenge,
        app_module.CustomerIdentity,
        app_module.CustomerAddress,
        app_module.Customer,
    ]
    with app_module.app.app_context():
        for model in models:
            model.query.delete()
        app_module.db.session.commit()
    yield
    with app_module.app.app_context():
        for model in models:
            model.query.delete()
        app_module.db.session.commit()

@pytest.fixture
def seeded_properties(app_module):
    with app_module.app.app_context():
        app_module.StayInventoryUnit.query.delete()
        app_module.StayRoomCategory.query.delete()
        app_module.StayProperty.query.delete()
        rows = [
            app_module.StayProperty(
                slug="public-jaipur-home", name="Public Jaipur Home", city="Jaipur",
                area="Sitapura", stay_types_json='["student"]', summary="Student living",
                active=True, public=True,
            ),
            app_module.StayProperty(
                slug="draft-jaipur-home", name="Draft Jaipur Home", city="Jaipur",
                area="Sitapura", stay_types_json='["student"]', summary="Draft",
                active=True, public=False,
            ),
            app_module.StayProperty(
                slug="public-gurugram-home", name="Public Gurugram Home", city="Gurugram",
                area="Sector 38", stay_types_json='["corporate","short_stay"]', summary="Corporate living",
                active=True, public=True,
            ),
        ]
        app_module.db.session.add_all(rows)
        app_module.db.session.commit()
    yield rows
    with app_module.app.app_context():
        app_module.StayInventoryUnit.query.delete()
        app_module.StayRoomCategory.query.delete()
        app_module.StayProperty.query.delete()
        app_module.db.session.commit()


@pytest.fixture
def seeded_inventory(app_module):
    with app_module.app.app_context():
        app_module.StayInventoryUnit.query.delete()
        app_module.StayRoomCategory.query.delete()
        app_module.StayProperty.query.delete()
        prop = app_module.StayProperty(
            slug="oasis-test", name="Oasis Test", city="Jaipur", area="Sitapura",
            stay_types_json='["student"]', summary="Test home", active=True, public=True,
        )
        app_module.db.session.add(prop)
        app_module.db.session.flush()
        category = app_module.StayRoomCategory(
            property_id=prop.id, slug="deluxe-twin", name="Deluxe Twin", occupancy=2,
            summary="Twin sharing", active=True,
        )
        app_module.db.session.add(category)
        app_module.db.session.flush()
        for idx in range(1, 5):
            app_module.db.session.add(app_module.StayInventoryUnit(
                property_id=prop.id,
                room_category_id=category.id,
                unit_type="room",
                code=f"R{idx}",
                display_name=f"Room {idx}",
                allocatable=True,
                active=(idx <= 3),
            ))
        app_module.db.session.commit()
    yield prop, category
    with app_module.app.app_context():
        app_module.StayInventoryUnit.query.delete()
        app_module.StayRoomCategory.query.delete()
        app_module.StayProperty.query.delete()
        app_module.db.session.commit()
