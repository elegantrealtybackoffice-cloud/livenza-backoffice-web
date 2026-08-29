from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_typed_api_client_uses_plan1_endpoints_and_error_contract():
    types=(WEB/'src/lib/types.ts'); api=(WEB/'src/lib/api.ts')
    assert types.exists() and api.exists()
    text=api.read_text()
    for endpoint in ['/api/v1/cities','/api/v1/properties','/api/v1/availability']:
        assert endpoint in text
    assert 'class ApiError' in text
    assert "cache: 'no-store'" in text


def test_stays_search_is_url_driven_and_has_all_three_intents():
    search=(WEB/'src/components/stays-search.tsx')
    assert search.exists()
    text=search.read_text()
    for label in ['College, area, landmark or property','student','corporate','short_stay','Find stays']:
        assert label in text
    assert 'URLSearchParams' in text
    assert "router.push(`/stays?${params.toString()}`)" in text


def test_stays_page_exposes_find_your_place_and_verified_results_only():
    page=(WEB/'src/app/stays/page.tsx')
    assert page.exists()
    text=page.read_text()
    assert 'FIND YOUR PLACE.' in text
    assert 'getCities' in text and 'getProperties' in text
    assert 'rating' not in text.lower()
