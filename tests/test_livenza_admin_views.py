from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT/'app.py').read_text(encoding='utf-8')
TEMPLATES = ROOT/'templates'

ROUTES = {
    '/admin/livenza/customers': 'customers',
    '/admin/livenza/properties': 'stays_admin',
    '/admin/livenza/bookings': 'stays_admin',
    '/admin/livenza/store/orders': 'store_admin',
    '/admin/livenza/support': 'customers',
}


def test_admin_routes_exist_with_module_permissions():
    for route, permission in ROUTES.items():
        marker = f"@app.route('{route}'"
        assert marker in APP
        block = APP.split(marker, 1)[1][:900]
        assert f"@permission_required('{permission}')" in block


def test_detail_and_mutation_routes_exist():
    expected = [
        "/admin/livenza/customers/<int:customer_id>",
        "/admin/livenza/properties/<int:property_id>",
        "/admin/livenza/bookings/<int:booking_id>",
        "/admin/livenza/store/orders/<int:order_id>",
        "/admin/livenza/support/<int:ticket_id>/status",
    ]
    for route in expected:
        assert route in APP


def test_admin_templates_exist_and_never_render_auth_hashes_or_private_keys():
    names = [
        'livenza_customers.html','livenza_customer_detail.html','livenza_properties.html',
        'livenza_property_edit.html','livenza_bookings.html','livenza_booking_detail.html',
        'livenza_store_admin.html','livenza_order_detail.html','livenza_support_admin.html',
    ]
    joined = ''
    for name in names:
        path = TEMPLATES/name
        assert path.exists(), name
        joined += path.read_text(encoding='utf-8')
    lowered = joined.lower()
    for forbidden in ['otp_hash', 'token_hash', 'storage_key']:
        assert forbidden not in lowered


def test_admin_landing_links_to_unified_operations():
    admin = (TEMPLATES/'admin.html').read_text(encoding='utf-8')
    for endpoint in ['livenza_customers_admin','livenza_properties_admin','livenza_bookings_admin','livenza_store_orders_admin','livenza_support_admin']:
        assert endpoint in admin


def test_unified_admin_home_is_reachable_without_replacing_legacy_admin_route():
    assert "@app.route('/admin/livenza')" in APP
    block=APP.split("@app.route('/admin/livenza')",1)[1][:700]
    assert '@login_required' in block
    assert "render_template('admin.html')" in block
