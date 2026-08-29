from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / 'livenza_api_v1.py').read_text(encoding='utf-8')
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')


def _block(name):
    return API_SOURCE.split(f'def {name}(', 1)[1].split('\n    @api.', 1)[0]


def test_public_catalogue_product_and_quote_routes_exist():
    for route in ['/products', '/products/<slug>', '/cart/quote']:
        assert route in API_SOURCE


def test_catalogue_only_exposes_public_active_products():
    block = _block('list_products')
    assert 'Product.public.is_(True)' in block
    assert 'Product.active.is_(True)' in block


def test_product_serializer_only_lists_active_variants():
    block = _block('_serialize_product')
    assert 'ProductVariant.active.is_(True)' in block


def test_cart_quote_is_server_authoritative_and_rejects_out_of_stock():
    block = _block('cart_quote')
    quote_helper = _block('_quote_items')
    assert 'price_minor' in quote_helper
    assert "item.get('price" not in quote_helper and 'item.get("price' not in quote_helper
    assert 'OUT_OF_STOCK' in block
    assert 'available_stock(' in quote_helper
    assert 'calculate_order_totals(' in quote_helper


def test_store_models_are_injected_into_api_registration():
    for name in ['Product','ProductVariant','StoreOrder','StoreOrderItem','LoyaltyAccount','LoyaltyLedgerEntry']:
        assert f"'{name}': {name}" in APP_SOURCE
