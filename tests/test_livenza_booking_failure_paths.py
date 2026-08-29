from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
WEB_ROOT=ROOT/'web/src'


def block(name):
    return API.split(f'def {name}',1)[1].split('\n    @api.',1)[0]


def test_expired_hold_cannot_start_payment():
    text=block('create_payment():')
    assert 'hold.expires_at <= now' in text
    assert 'hold_expired' in text


def test_failed_payment_never_confirms_booking():
    text=block('razorpay_webhook():')
    failed=text.split('if next_state == "failed":',1)[1].split('if next_state == "paid":',1)[0]
    assert 'confirmed' not in failed
    assert 'payment.status = "failed"' in failed


def test_duplicate_webhook_is_noop_before_processing():
    text=block('razorpay_webhook():')
    duplicate=text.index('ProcessedWebhookEvent.query.filter_by')
    parsing=text.index('json.loads(raw_body.decode')
    assert duplicate < parsing
    assert 'duplicate=True' in text


def test_no_inventory_has_stable_409_code():
    text=block('booking_hold():')
    assert '409, "NO_AVAILABILITY"' in text


def test_unauthorized_parent_share_creation_is_forbidden():
    text=block('create_parent_share(public_id):')
    assert 'booking.customer_id != customer.id' in text
    assert '403' in text and 'booking_not_owned' in text


def test_receipt_is_scoped_to_authenticated_customer():
    text=block('booking_receipt(public_id):')
    assert 'customer_id=customer.id' in text
    assert 'payment.status != "paid"' in text


def test_frontend_never_contains_razorpay_secret_names():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in WEB_ROOT.rglob('*') if p.is_file() and p.suffix in {'.ts','.tsx','.js','.mjs'})
    assert 'RAZORPAY_KEY_SECRET' not in combined
    assert 'RAZORPAY_WEBHOOK_SECRET' not in combined


def test_browser_success_callback_only_navigates_and_does_not_mark_confirmed():
    wizard=(ROOT/'web/src/components/booking/booking-wizard.tsx').read_text(encoding='utf-8')
    handler=wizard.split('handler:',1)[1].split('modal:',1)[0]
    assert 'router.push' in handler
    assert 'confirmed' not in handler
