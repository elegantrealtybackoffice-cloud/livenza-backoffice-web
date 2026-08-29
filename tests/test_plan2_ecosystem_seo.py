from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_future_verticals_are_named_and_explicitly_early_access():
    for name in ['fit','groom','skin','media']:
        p=WEB/f'src/app/{name}/page.tsx'
        assert p.exists(), f'missing {name} page'
        t=p.read_text()
        assert f'livenza.{name}' in t.lower()
        assert 'EARLY ACCESS' in t
        assert '<form' not in t.lower()
        assert '/contact' in t


def test_operational_shell_routes_have_pages_or_safe_handoff():
    for route in ['store','about','life','contact','account','stays/book']:
        assert (WEB/f'src/app/{route}/page.tsx').exists(), f'missing route {route}'


def test_seo_sitemap_robots_and_analytics_contracts_exist():
    for rel in ['src/app/sitemap.ts','src/app/robots.ts','src/lib/seo.ts','src/lib/analytics.ts']:
        assert (WEB/rel).exists(), rel
    sitemap=(WEB/'src/app/sitemap.ts').read_text()
    for route in ["'/'","'/stays'","'/store'","'/fit'","'/groom'","'/skin'","'/media'"]:
        assert route in sitemap
    analytics=(WEB/'src/lib/analytics.ts').read_text()
    for event in ['homepage_view','stays_search','property_view','availability_check','room_select','booking_start','parent_share','booking_payment_start','booking_complete','store_view','product_view','add_to_cart','checkout_start','purchase','signup','login','support_request']:
        assert f"'{event}'" in analytics
    assert 'export function track' in analytics
    assert 'try {' in analytics


def test_home_wires_nonblocking_homepage_analytics():
    page=(WEB/'src/app/page.tsx').read_text()
    assert 'HomepageAnalytics' in page
    component=(WEB/'src/components/homepage-analytics.tsx').read_text()
    assert "track('homepage_view')" in component
