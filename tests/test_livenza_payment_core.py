import hashlib
import hmac
import pytest

from livenza_payment_core import verify_razorpay_webhook, payment_event_state, public_gateway_config


def test_webhook_verification_uses_raw_body():
    raw = b'{"event":"payment.captured"}'
    secret = 'whsec-test'
    signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    assert verify_razorpay_webhook(raw, signature, secret)
    assert not verify_razorpay_webhook(raw + b' ', signature, secret)


def test_payment_events_converge_without_confirming_failure():
    assert payment_event_state('payment.captured') == 'paid'
    assert payment_event_state('order.paid') == 'paid'
    assert payment_event_state('payment.failed') == 'failed'
    assert payment_event_state('payment.authorized') == 'pending'
    assert payment_event_state('other') is None


def test_public_gateway_config_never_returns_secret():
    cfg = public_gateway_config({'key_id':'rzp_test_public','key_secret':'private','webhook_secret':'private-hook'})
    assert cfg == {'key_id':'rzp_test_public'}
    assert 'secret' not in repr(cfg).lower()
