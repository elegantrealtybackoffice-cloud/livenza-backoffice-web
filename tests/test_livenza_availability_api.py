from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / "livenza_api_v1.py").read_text(encoding="utf-8")


def test_availability_route_and_date_validation_exist():
    assert '@api.get("/availability")' in API_SOURCE
    assert "datetime.date.fromisoformat" in API_SOURCE
    assert "if end <= start:" in API_SOURCE


def test_availability_counts_only_active_allocatable_category_units():
    for fragment in [
        "room_category_id=category.id",
        "allocatable=True",
        "active=True",
        "available_count=count",
        "availability_state=availability_state(count, 0)",
    ]:
        assert fragment in API_SOURCE


def test_runtime_availability_counts_active_units_when_flask_is_available(client, seeded_inventory):
    res = client.get(
        "/api/v1/availability?property=oasis-test&room_category=deluxe-twin&start=2026-09-01&end=2026-09-30"
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["available_count"] == 3
    assert body["availability_state"] == "available"
    assert body["allocatable_unit_type"] == "room"


def test_runtime_invalid_date_range_is_rejected_when_flask_is_available(client, seeded_inventory):
    res = client.get(
        "/api/v1/availability?property=oasis-test&room_category=deluxe-twin&start=2026-09-30&end=2026-09-01"
    )
    assert res.status_code == 400
