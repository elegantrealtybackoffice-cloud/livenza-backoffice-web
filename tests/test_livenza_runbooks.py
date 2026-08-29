from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGING=ROOT/'docs/runbooks/livenza-v1-staging.md'
PROD=ROOT/'docs/runbooks/livenza-v1-production.md'
VERIFY=ROOT/'scripts/livenza_postdeploy_verify.py'
APP=(ROOT/'app.py').read_text(encoding='utf-8')


def test_staging_runbook_has_required_order_and_seven_gates():
    assert STAGING.exists(); text=STAGING.read_text(encoding='utf-8')
    required=['backup','Plan 1','Plan 3','Plan 4','Plan 5','Razorpay Test Mode','Playwright','legacy migration dry-run']
    for phrase in required: assert phrase.lower() in text.lower()
    for gate in ['Brand','Functional','Commercial','Data','Payments','Responsive','Performance']:
        assert gate in text


def test_production_runbook_has_rollback_and_live_validation_steps():
    assert PROD.exists(); text=PROD.read_text(encoding='utf-8')
    for phrase in ['backup','additive migrations','smoke back-office','consumer web','post-deploy','rollback consumer routing','Razorpay']:
        assert phrase.lower() in text.lower()


def test_postdeploy_verifier_uses_env_secrets_and_optional_booking_order_checks():
    assert VERIFY.exists(); text=VERIFY.read_text(encoding='utf-8')
    assert 'LIVENZA_POSTDEPLOY_TOKEN' in text
    assert '--booking-id' in text and '--order-id' in text
    assert '/admin/livenza/postdeploy/verify/' in text
    assert 'Authorization' in text


def test_postdeploy_endpoint_uses_constant_time_token_check_and_returns_no_pii():
    assert '/admin/livenza/postdeploy/verify/<kind>/<public_id>' in APP
    block=APP.split('/admin/livenza/postdeploy/verify/<kind>/<public_id>',1)[1].split("@app.route('/admin/livenza/customers')",1)[0]
    assert 'hmac.compare_digest' in block
    for pii in ['primary_mobile','primary_email','full_name']:
        assert pii not in block
