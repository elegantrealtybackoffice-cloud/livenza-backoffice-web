import hashlib
import hmac
import re
import secrets


def normalize_mobile(value: str, default_country_code: str = "+91") -> str:
    raw = (value or "").strip()
    has_plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValueError("mobile is required")
    if has_plus:
        normalized = "+" + digits
    elif len(digits) == 10:
        normalized = default_country_code + digits
    elif digits.startswith("91") and len(digits) == 12:
        normalized = "+" + digits
    else:
        raise ValueError("unsupported mobile format")
    if len(re.sub(r"\D", "", normalized)) < 10:
        raise ValueError("mobile is too short")
    return normalized


def normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("valid email is required")
    return email


def hash_otp(identifier: str, otp: str, salt: str) -> str:
    message = f"{identifier}\0{otp}\0{salt}".encode("utf-8")
    return hashlib.sha256(message).hexdigest()


def verify_otp(identifier: str, otp: str, salt: str, expected_hash: str) -> bool:
    actual = hash_otp(identifier, otp, salt)
    return hmac.compare_digest(actual, expected_hash or "")


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()
