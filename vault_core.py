import base64, hashlib, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ALLOWED_SECRET_TYPES={
    'electricity_login','bbps_api_secret','payment_api_secret','operational_api_secret'
}
FORBIDDEN_SECRET_TYPES={
    'bank_password','upi_pin','card_pin','cvv','otp','captcha','bank_session_cookie'
}

def _key_bytes(master_key:str)->bytes:
    value=(master_key or '').strip()
    if len(value)<24:
        raise ValueError('LIVENZA_VAULT_MASTER_KEY must contain at least 24 characters.')
    return hashlib.sha256(value.encode('utf-8')).digest()

def validate_secret_type(secret_type:str)->str:
    value=(secret_type or '').strip().lower()
    if value in FORBIDDEN_SECRET_TYPES or value not in ALLOWED_SECRET_TYPES:
        raise ValueError('This secret type is not allowed in Livenza Vault.')
    return value

def encrypt_secret(plaintext:str, master_key:str):
    key=_key_bytes(master_key); nonce=os.urandom(12)
    ciphertext=AESGCM(key).encrypt(nonce,(plaintext or '').encode('utf-8'),b'livenza-vault-v1')
    return base64.b64encode(ciphertext).decode('ascii'),base64.b64encode(nonce).decode('ascii')

def decrypt_secret(ciphertext_b64:str, nonce_b64:str, master_key:str)->str:
    key=_key_bytes(master_key)
    ciphertext=base64.b64decode(ciphertext_b64); nonce=base64.b64decode(nonce_b64)
    return AESGCM(key).decrypt(nonce,ciphertext,b'livenza-vault-v1').decode('utf-8')

def mask_secret(value:str)->str:
    value=value or ''; return '••••••••'+(value[-4:] if value else '')

def encrypt_blob(raw:bytes, master_key:str):
    key=_key_bytes(master_key)
    nonce=os.urandom(12)
    ciphertext=AESGCM(key).encrypt(nonce,raw or b'',b'livenza-master-doc-v1')
    return base64.b64encode(ciphertext).decode('ascii'),base64.b64encode(nonce).decode('ascii')

def decrypt_blob(ciphertext_b64:str, nonce_b64:str, master_key:str)->bytes:
    key=_key_bytes(master_key)
    ciphertext=base64.b64decode(ciphertext_b64)
    nonce=base64.b64decode(nonce_b64)
    return AESGCM(key).decrypt(nonce,ciphertext,b'livenza-master-doc-v1')
