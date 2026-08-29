from pathlib import Path
import importlib.util
import tempfile

ROOT=Path(__file__).resolve().parents[1]
STORAGE=ROOT/'livenza_storage.py'
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
APP=(ROOT/'app.py').read_text(encoding='utf-8')


def load_storage():
    spec=importlib.util.spec_from_file_location('livenza_storage',STORAGE)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_storage_key_normalization_rejects_traversal():
    mod=load_storage()
    for bad in ['../secret','/absolute','a/../../b','']:
        try: mod.normalize_key(bad)
        except ValueError: pass
        else: raise AssertionError(bad)
    assert mod.normalize_key('customers/12/agreement.pdf')=='customers/12/agreement.pdf'


def test_local_adapter_private_and_public_contracts():
    mod=load_storage()
    with tempfile.TemporaryDirectory() as tmp:
        adapter=mod.LocalStorageAdapter(tmp)
        adapter.put_private('private/a.txt',b'hello','text/plain')
        adapter.put_public('public/b.txt',b'world','text/plain')
        signed=adapter.signed_get_url('private/a.txt',expires_seconds=60)
        assert signed.startswith('file://') and 'private/a.txt' in signed
        assert adapter.public_url('public/b.txt').startswith('file://')


def test_owner_document_download_route_uses_signed_url_not_raw_key():
    assert '@api.get("/me/documents/<int:document_id>/download")' in API
    block=API.split('@api.get("/me/documents/<int:document_id>/download")',1)[1][:1800]
    assert 'session_for_request()' in block
    assert 'document.customer_id != customer.id' in block
    assert 'signed_get_url' in block
    assert 'storage_key' not in block.split('return jsonify',1)[1] if 'return jsonify' in block else True


def test_property_media_is_injected_and_public_detail_serializes_url():
    assert "'PropertyMedia': PropertyMedia" in APP
    assert 'PropertyMedia = models["PropertyMedia"]' in API
    detail=API.split('def public_property_detail',1)[1][:4000]
    assert 'PropertyMedia.query' in detail
    assert 'public_url' in detail
