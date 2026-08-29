from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / 'livenza_api_v1.py').read_text(encoding='utf-8')
INTEGRATIONS = (ROOT / 'livenza_integrations.py').read_text(encoding='utf-8') if (ROOT/'livenza_integrations.py').exists() else ''
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_payment_routes_are_defined():
    for route in ['/payments', '/payments/webhooks/razorpay', '/payments/<public_id>']:
        assert route in API_SOURCE


def test_webhook_reads_raw_body_before_parsing_json_and_checks_event_id():
    block = API_SOURCE.split('def razorpay_webhook():',1)[1].split('\n    @api.',1)[0]
    raw_pos = block.index('request.get_data(cache=False, as_text=False)')
    verify_pos = block.index('verify_razorpay_webhook')
    parse_pos = block.index('json.loads(raw_body.decode')
    assert raw_pos < verify_pos < parse_pos
    assert 'x-razorpay-event-id' in block.lower()
    assert 'duplicate' in block


def test_payment_failed_path_never_confirms_booking():
    block = API_SOURCE.split('def razorpay_webhook():',1)[1].split('\n    @api.',1)[0]
    failed = block.split('if next_state == "failed":',1)[1].split('if next_state == "paid":',1)[0]
    assert 'booking.status = "confirmed"' not in failed
    assert 'payment.status = "failed"' in failed


def test_paid_path_converts_hold_exactly_once():
    block = API_SOURCE.split('def _confirm_booking_payment',1)[1].split('\n    def ',1)[0]
    assert 'if booking.status == "confirmed"' in block
    assert 'hold.status == "active"' in block
    assert 'hold.status = "converted"' in block


def test_gateway_credentials_are_server_only():
    assert 'RAZORPAY_KEY_SECRET' in INTEGRATIONS
    assert 'RAZORPAY_WEBHOOK_SECRET' in INTEGRATIONS
    assert 'key_secret' not in API_SOURCE.split('def create_payment()',1)[1].split('\n    @api.',1)[0]


def test_api_registration_injects_payment_models():
    for name in ['PaymentRecord','ProcessedWebhookEvent']:
        assert f"'{name}': {name}" in APP_SOURCE
