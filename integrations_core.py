"""Pure-domain helpers for the Livenza v1.8.0 Integrations Center.

This module intentionally has no Flask/SQLAlchemy dependency so policy can be tested
without a running web application.
"""
from __future__ import annotations

import json
from urllib.parse import urlparse

CATEGORY_MODULES = {
    'ai': 'integrations',
    'whatsapp': 'whatsapp',
    'google_email': 'email',
    'google_drive': 'drive',
    'food': 'food',
    'electricity': 'electricity',
    'banking': 'banking',
    'billing': 'rentok',
    'payments': 'integrations',
    'webhooks': 'integrations',
}

PROHIBITED_CONFIG_KEYS = {
    'password', 'bank_password', 'upi_pin', 'pin', 'card_pin', 'cvv',
    'otp', 'captcha', 'captcha_answer', 'session_cookie', 'banking_session_cookie',
    'api_key', 'api_token', 'access_token', 'refresh_token', 'client_secret',
}

# These names may be Vault-backed integration secrets. Restricted banking/auth factors
# are never accepted, even though generic API credentials are allowed.
ALLOWED_SECRET_NAMES = {
    'api_key', 'api_token', 'access_token', 'refresh_token', 'client_secret',
    'client_id_secret', 'webhook_secret', 'signing_secret', 'provider_secret',
    'oauth_client_secret', 'bbps_client_secret', 'payment_client_secret',
    'whatsapp_access_token', 'google_refresh_token', 'openai_api_key',
}
FORBIDDEN_SECRET_NAMES = {
    'password', 'bank_password', 'upi_pin', 'pin', 'card_pin', 'cvv', 'otp',
    'captcha', 'captcha_answer', 'session_cookie', 'banking_session_cookie',
}

URL_KEY_HINTS = ('url', 'uri', 'endpoint', 'callback', 'webhook')
SAFE_SUMMARY_KEYS = {
    'id', 'provider_id', 'display_name', 'category', 'status', 'source_mode',
    'property_scope', 'last_test_status', 'last_test_message', 'last_tested_at',
    'last_success_status', 'last_success_message', 'last_success_at', 'active',
    'config', 'nonsecret_config', 'portal_url', 'provider_key', 'workflow_module',
}

def category_module(category: str) -> str:
    return CATEGORY_MODULES.get((category or '').strip().lower(), 'integrations')


def user_can_access_category(user_modules, category: str, is_admin: bool = False) -> bool:
    if is_admin:
        return True
    modules = {str(x).strip() for x in (user_modules or set()) if str(x).strip()}
    required = category_module(category)
    return bool(required and required in modules)


def _json_safe(value):
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('Integration configuration must be JSON-serializable.') from exc
    return value


def _validate_url(value: str) -> str:
    value = (value or '').strip()
    if not value:
        return ''
    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError('Integration URLs must use http:// or https://.')
    return value


def normalize_nonsecret_config(payload) -> dict:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError('Integration configuration must be an object.')
    out = {}
    for raw_key, raw_value in payload.items():
        key = str(raw_key or '').strip()
        compare = key.lower()
        if not key:
            continue
        if compare in PROHIBITED_CONFIG_KEYS:
            raise ValueError(f'{key} is a secret and must be stored in Livenza Vault.')
        value = raw_value.strip() if isinstance(raw_value, str) else raw_value
        if isinstance(value, str) and any(hint in compare for hint in URL_KEY_HINTS):
            value = _validate_url(value)
        out[key] = _json_safe(value)
    return out


def safe_connection_summary(row) -> dict:
    if row is None:
        return {}
    if hasattr(row, '__dict__'):
        source = dict(row.__dict__)
    else:
        source = dict(row)
    result = {}
    for key in SAFE_SUMMARY_KEYS:
        if key in source:
            value = source[key]
            if key in ('config', 'nonsecret_config') and isinstance(value, dict):
                value = normalize_nonsecret_config(value)
            result[key] = value
    # SQLAlchemy stores config as JSON text; expose only parsed non-secret content.
    raw = source.get('nonsecret_config_json')
    if raw and 'nonsecret_config' not in result:
        try:
            parsed = json.loads(raw)
            result['nonsecret_config'] = normalize_nonsecret_config(parsed if isinstance(parsed, dict) else {})
        except Exception:
            result['nonsecret_config'] = {}
    return result


def validate_integration_secret_name(name: str) -> str:
    value = (name or '').strip().lower().replace(' ', '_')
    if not value:
        raise ValueError('Secret name is required.')
    if value in FORBIDDEN_SECRET_NAMES or value.startswith('bank_password'):
        raise ValueError('Restricted authentication factors cannot be stored in Integrations Center.')
    if value not in ALLOWED_SECRET_NAMES and not value.endswith(('_secret', '_token', '_api_key')):
        raise ValueError('Unsupported integration secret name.')
    return value
