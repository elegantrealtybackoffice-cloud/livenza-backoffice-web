from pathlib import Path
from types import SimpleNamespace
import livenza_api_v1

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / "livenza_api_v1.py").read_text(encoding="utf-8")


def test_public_routes_are_defined():
    for route in ['/cities', '/properties', '/properties/<slug>']:
        assert route in API_SOURCE


def test_property_serializer_is_explicit_and_safe():
    row = SimpleNamespace(
        id=7, slug="oasis-test", name="Oasis Test", city="Jaipur", area="Sitapura",
        summary="Student living", stay_types=["student"],
        password_hash="secret", ciphertext="secret",
    )
    payload = livenza_api_v1.serialize_property(row)
    assert payload == {
        "id": 7,
        "slug": "oasis-test",
        "name": "Oasis Test",
        "city": "Jaipur",
        "area": "Sitapura",
        "summary": "Student living",
        "stay_types": ["student"],
    }


def test_public_queries_require_active_and_public_properties():
    assert "StayProperty.query.filter_by(active=True, public=True)" in API_SOURCE
    assert "filter_by(slug=slug, active=True, public=True)" in API_SOURCE


def test_private_property_is_not_publicly_listed_when_flask_is_available(client, seeded_properties):
    res = client.get("/api/v1/properties?city=Jaipur")
    assert res.status_code == 200
    names = [row["name"] for row in res.get_json()["items"]]
    assert "Public Jaipur Home" in names
    assert "Draft Jaipur Home" not in names


def test_nonpublic_property_detail_is_404_when_flask_is_available(client, seeded_properties):
    assert client.get("/api/v1/properties/draft-jaipur-home").status_code == 404


def test_city_list_is_derived_from_public_properties_when_flask_is_available(client, seeded_properties):
    res = client.get("/api/v1/cities")
    assert {row["name"] for row in res.get_json()["items"]} == {"Jaipur", "Gurugram"}
