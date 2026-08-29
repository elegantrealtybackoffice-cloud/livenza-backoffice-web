from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / 'livenza_api_v1.py').read_text(encoding='utf-8')
PAYMENT = (ROOT / 'livenza_payment_core.py').read_text(encoding='utf-8')


def _block(name):
    return API.split(f'def {name}(', 1)[1].split('\n    @api.', 1)[0]


def test_order_creation_route_is_authenticated_and_locks_variants():
    assert '/orders' in API
    block = _block('create_store_order')
    assert 'session_for_request()' in block
    assert 'authentication_required' in block
    assert 'with_for_update()' in _block('_locked_variants')
    assert 'stock_reserved' in block
    assert 'PaymentRecord(' in block
    assert 'source_type="store_order"' in block


def test_paid_store_payment_converts_reserved_stock_once():
    block = _block('_confirm_store_order_payment')
    assert "payment.source_type != 'store_order'" in block
    assert "order.status == 'confirmed'" in block
    assert 'stock_on_hand' in block
    assert 'stock_reserved' in block
    assert 'transition_order(' in block


def test_failed_store_payment_releases_reservation():
    block = _block('_release_store_order_payment')
    assert 'stock_reserved' in block
    assert "order.status != 'placed'" in block
    assert "order.status = 'cancelled'" in block


def test_webhook_dispatches_booking_and_store_sources():
    block = _block('razorpay_webhook')
    assert '_confirm_payment_source(payment)' in block
    assert '_release_payment_source(payment)' in block
    assert 'store_order' in API


def test_payment_core_documents_supported_source_types():
    assert 'SUPPORTED_PAYMENT_SOURCES' in PAYMENT
    assert "'booking'" in PAYMENT and "'store_order'" in PAYMENT
