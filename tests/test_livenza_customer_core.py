from livenza_customer_core import (
    normalize_mobile, normalize_email, hash_otp, verify_otp,
    new_session_token, hash_session_token,
)


def test_indian_mobile_is_normalized_to_e164():
    assert normalize_mobile("98765 43210") == "+919876543210"
    assert normalize_mobile("+91-98765-43210") == "+919876543210"


def test_email_is_trimmed_and_lowercased():
    assert normalize_email(" Rishabh@Example.COM ") == "rishabh@example.com"


def test_otp_hash_is_identifier_bound_and_verifiable():
    digest = hash_otp("+919876543210", "482913", "salt-1")
    assert verify_otp("+919876543210", "482913", "salt-1", digest)
    assert not verify_otp("+919876543210", "482914", "salt-1", digest)
    assert not verify_otp("+919999999999", "482913", "salt-1", digest)


def test_session_token_is_random_and_only_hash_is_persisted():
    first = new_session_token()
    second = new_session_token()
    assert first != second
    assert len(first) >= 32
    assert hash_session_token(first) != first
