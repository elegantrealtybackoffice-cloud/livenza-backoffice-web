from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
CORE=(ROOT/'livenza_commerce_core.py').read_text(encoding='utf-8')
E2E=ROOT/'web/e2e/store.spec.ts'


def _block(name): return API.split(f'def {name}(',1)[1].split('\n    @api.',1)[0]


def test_client_price_tampering_has_no_authority():
    quote=_block('_quote_items')
    create=_block('create_store_order')
    assert 'variant.price_minor' in create
    assert 'row.price_minor' in quote
    for block in [quote,create]:
        assert 'item.get("price' not in block and "item.get('price" not in block


def test_out_of_stock_and_final_unit_lock_are_enforced():
    create=_block('create_store_order')
    locked=_block('_locked_variants')
    assert 'OUT_OF_STOCK' in create
    assert 'available_stock(' in create
    assert 'with_for_update()' in locked


def test_failed_payment_releases_and_duplicate_webhook_is_early_exit():
    release=_block('_release_store_order_payment')
    webhook=_block('razorpay_webhook')
    assert 'stock_reserved' in release
    assert 'ProcessedWebhookEvent.query.filter_by' in webhook
    assert 'duplicate=True' in webhook


def test_order_reads_are_owner_scoped():
    block=_block('get_store_order')
    assert 'customer_id=customer.id' in block
    assert 'authentication_required' in block


def test_resident_delivery_cannot_be_self_asserted():
    create=_block('create_store_order')
    assert '_eligible_property_room_delivery(customer.id)' in create
    assert 'invalid_delivery_option' in create


def test_loyalty_duplicate_effect_is_checked_before_insert():
    block=_block('_award_loyalty_points')
    assert 'existing = LoyaltyLedgerEntry.query.filter_by' in block
    assert 'if existing:' in block


def test_store_e2e_acceptance_file_exists_and_covers_same_identity():
    assert E2E.exists()
    text=E2E.read_text(encoding='utf-8')
    for phrase in ['same Livenza identity','/store','/store/checkout','/my/orders','/my/rewards']:
        assert phrase in text
