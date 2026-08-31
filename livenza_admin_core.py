"""Pure safety helpers for privileged Livenza admin actions."""
from __future__ import annotations

ALLOWED_AUDIT_KEYS = {
    'booking_id','order_id','payment_id','variant_id','content_id','customer_id','property_id',
    'from_status','to_status','event','amount_minor','refund_amount_minor','quantity_delta',
    'reason','reason_code','provider_reference','source_type','source_id','public_id','sku',
}
SENSITIVE_FRAGMENTS = (
    'password','secret','token','otp','pin','cvv','captcha','cookie','credential','aadhaar',
    'pan','identity_number','storage_key','document_content','raw_body','authorization',
)


def audit_meta(payload: dict) -> dict:
    """Return a shallow, allow-listed metadata object safe for AuditEvent storage."""
    if not isinstance(payload, dict):
        return {}
    out = {}
    for key, value in payload.items():
        name = str(key).strip()
        lowered = name.lower()
        if name not in ALLOWED_AUDIT_KEYS:
            continue
        if any(fragment in lowered for fragment in SENSITIVE_FRAGMENTS):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[name] = value if not isinstance(value, str) else value[:500]
    return out


def production_config_errors(env) -> list[str]:
    """Return blocking production configuration errors; non-production is intentionally permissive."""
    get=lambda key,default='': str((env or {}).get(key,default) or '').strip()
    environment=(get('LIVENZA_ENV') or get('FLASK_ENV') or get('ENVIRONMENT')).lower()
    if environment not in {'production','prod'}:
        return []
    errors=[]
    secret=get('SECRET_KEY')
    if len(secret)<32 or secret in {'change-this-secret-before-production','replace-me','replace-with-a-long-random-value','ChangeMeNow!2026'}:
        errors.append('SECRET_KEY must be a non-default random value of at least 32 characters.')
    database=get('DATABASE_URL')
    if not (database.startswith('postgresql://') or database.startswith('postgres://')):
        errors.append('DATABASE_URL must use PostgreSQL in production.')
    if get('FORCE_HTTPS','1')!='1':
        errors.append('FORCE_HTTPS must be enabled in production.')
    if get('CUSTOMER_AUTH_TEST_MODE','0')=='1':
        errors.append('CUSTOMER_AUTH_TEST_MODE cannot be enabled in production.')
    if get('CASHFREE_TEST_STUB','0')=='1':
        errors.append('CASHFREE_TEST_STUB cannot be enabled in production.')
    if get('RADIUS_TEST_STUB','0')=='1':
        errors.append('RADIUS_TEST_STUB cannot be enabled in production.')
    cashfree_env=get('CASHFREE_ENVIRONMENT','production').lower()
    if cashfree_env not in {'production','prod','live'}:
        errors.append('CASHFREE_ENVIRONMENT must be production in production.')
    if not get('CASHFREE_CLIENT_ID') or not get('CASHFREE_CLIENT_SECRET'):
        errors.append('Cashfree production client ID and client secret are required in production.')
    if get('RADIUS_ENABLED','0')=='1':
        radius_required=('RADIUS_BASE_URL','RADIUS_AUTH_TOKEN','RADIUS_SNAPSHOT_PATH','RADIUS_RECHARGE_PATH','RADIUS_STATUS_PATH')
        if not get('RADIUS_BASE_URL').startswith('https://') or any(not get(key) for key in radius_required[1:]):
            errors.append('Radius live integration requires an HTTPS base URL, auth token, snapshot path, recharge path and status path.')
    if not (get('SUPABASE_URL').startswith('https://') and get('SUPABASE_SERVICE_ROLE_KEY') and get('LIVENZA_PRIVATE_BUCKET')):
        errors.append('Private object storage must be configured in production.')
    return errors
