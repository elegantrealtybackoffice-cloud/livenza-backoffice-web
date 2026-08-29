"""Storage adapters for Livenza public media and private customer documents."""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen


def normalize_key(key: str) -> str:
    raw = str(key or '').strip().replace('\\', '/')
    if not raw or raw.startswith('/'):
        raise ValueError('A relative object key is required.')
    path = PurePosixPath(raw)
    if any(part in {'', '.', '..'} for part in path.parts):
        raise ValueError('Unsafe object key.')
    normalized = path.as_posix()
    if normalized.startswith('../') or '/..' in normalized:
        raise ValueError('Unsafe object key.')
    return normalized


class LocalStorageAdapter:
    """Filesystem backend for local tests/development only."""
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        normalized = normalize_key(key)
        target = (self.root / normalized).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError('Unsafe object key.')
        return target

    def _put(self, key: str, data: bytes, content_type: str) -> None:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes(data))

    def put_private(self, key: str, data: bytes, content_type: str) -> None:
        self._put(key, data, content_type)

    def put_public(self, key: str, data: bytes, content_type: str) -> None:
        self._put(key, data, content_type)

    def signed_get_url(self, key: str, expires_seconds: int = 300) -> str:
        target = self._path(key)
        if not target.exists():
            raise FileNotFoundError(normalize_key(key))
        return target.as_uri()

    def public_url(self, key: str) -> str:
        target = self._path(key)
        return target.as_uri() if target.exists() else ''


class SupabaseStorageAdapter:
    """Supabase Storage adapter using separate public/private buckets."""
    def __init__(self, base_url: str, service_key: str, private_bucket: str, public_bucket: str):
        self.base_url = base_url.rstrip('/')
        self.service_key = service_key.strip()
        self.private_bucket = private_bucket.strip()
        self.public_bucket = public_bucket.strip()
        if not self.base_url.startswith('https://') or not self.service_key or not self.private_bucket or not self.public_bucket:
            raise ValueError('Supabase storage configuration is incomplete.')

    def _headers(self, content_type='application/json'):
        return {'Authorization': f'Bearer {self.service_key}', 'apikey': self.service_key, 'Content-Type': content_type}

    def _upload(self, bucket: str, key: str, data: bytes, content_type: str):
        normalized = normalize_key(key)
        target = f"{self.base_url}/storage/v1/object/{quote(bucket,safe='')}/{quote(normalized,safe='/')}"
        headers = self._headers(content_type); headers['x-upsert'] = 'true'
        req = Request(target, data=bytes(data), headers=headers, method='POST')
        with urlopen(req, timeout=20) as response:
            if response.status >= 300:
                raise RuntimeError('Object upload failed.')

    def put_private(self, key: str, data: bytes, content_type: str) -> None:
        self._upload(self.private_bucket, key, data, content_type)

    def put_public(self, key: str, data: bytes, content_type: str) -> None:
        self._upload(self.public_bucket, key, data, content_type)

    def signed_get_url(self, key: str, expires_seconds: int = 300) -> str:
        normalized = normalize_key(key)
        target = f"{self.base_url}/storage/v1/object/sign/{quote(self.private_bucket,safe='')}/{quote(normalized,safe='/')}"
        payload = json.dumps({'expiresIn': max(int(expires_seconds), 30)}).encode('utf-8')
        req = Request(target, data=payload, headers=self._headers(), method='POST')
        with urlopen(req, timeout=15) as response:
            body = json.loads(response.read().decode('utf-8') or '{}')
        signed = body.get('signedURL') or body.get('signedUrl') or ''
        if not signed:
            raise RuntimeError('Storage provider did not return a signed URL.')
        return signed if signed.startswith('http') else f"{self.base_url}/storage/v1{signed}"

    def public_url(self, key: str) -> str:
        normalized = normalize_key(key)
        return f"{self.base_url}/storage/v1/object/public/{quote(self.public_bucket,safe='')}/{quote(normalized,safe='/')}"


class UnconfiguredStorageAdapter:
    def _raise(self, *args, **kwargs):
        raise RuntimeError('Livenza object storage is not configured.')
    put_private = _raise
    put_public = _raise
    signed_get_url = _raise
    def public_url(self, key: str) -> str:
        return ''


def storage_from_env():
    backend = (os.getenv('LIVENZA_STORAGE_BACKEND') or '').strip().lower()
    environment = (os.getenv('LIVENZA_ENV') or os.getenv('FLASK_ENV') or '').strip().lower()
    if backend == 'local' and environment in {'test','testing','development','dev','local'}:
        return LocalStorageAdapter(os.getenv('LIVENZA_LOCAL_STORAGE_DIR') or './instance/livenza-storage')
    base = (os.getenv('SUPABASE_URL') or '').strip()
    key = (os.getenv('SUPABASE_SERVICE_ROLE_KEY') or '').strip()
    if base and key:
        return SupabaseStorageAdapter(
            base, key,
            os.getenv('LIVENZA_PRIVATE_BUCKET') or 'livenza-private',
            os.getenv('LIVENZA_PUBLIC_BUCKET') or 'livenza-public',
        )
    return UnconfiguredStorageAdapter()
