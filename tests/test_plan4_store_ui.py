from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'


def read(rel): return (WEB / rel).read_text(encoding='utf-8')


def test_store_routes_and_components_exist():
    required = [
        'src/app/store/page.tsx',
        'src/app/store/[collection]/page.tsx',
        'src/app/store/product/[slug]/page.tsx',
        'src/app/store/cart/page.tsx',
        'src/app/store/checkout/page.tsx',
        'src/app/store/order/[orderId]/page.tsx',
        'src/components/store/storefront.tsx',
        'src/components/store/product-detail.tsx',
        'src/components/store/cart-view.tsx',
        'src/components/store/checkout-view.tsx',
    ]
    for rel in required:
        assert (WEB / rel).exists(), rel


def test_store_home_uses_four_launch_worlds_and_editorial_copy():
    text = read('src/components/store/storefront.tsx')
    for world in ['Wear','Move','Live','Accessories']:
        assert world in text
    assert 'WEAR THE LIFE.' in text
    assert 'store_view' in text


def test_cart_persists_only_variant_ids_and_quantities_and_refreshes_quote():
    text = read('src/components/store/cart-view.tsx')
    assert 'variant_id' in text and 'quantity' in text
    assert 'unit_price_minor' not in text.split('localStorage.setItem',1)[1].split(')',1)[0]
    assert 'quoteCart' in text


def test_checkout_requotes_and_uses_backend_order_before_success():
    text = read('src/components/store/checkout-view.tsx')
    assert 'quoteCart' in text
    assert 'createStoreOrder' in text
    assert 'checkout_start' in text
    assert 'OUT_OF_STOCK' in text
    assert 'order.status' in text or 'getStoreOrder' in text


def test_store_api_types_and_analytics_are_wired():
    api = read('src/lib/api.ts')
    types = read('src/lib/types.ts')
    analytics = read('src/lib/analytics.ts')
    for fn in ['getProducts','getProduct','quoteCart','createStoreOrder','getStoreOrder']:
        assert f'function {fn}' in api or f'async function {fn}' in api
    for name in ['StoreProduct','StoreVariant','StoreOrder','CartQuote']:
        assert f'type {name}' in types
    for event in ['store_view','product_view','add_to_cart','checkout_start','purchase']:
        assert event in analytics
