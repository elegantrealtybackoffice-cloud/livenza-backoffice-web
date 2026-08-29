from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
WEB_API=(ROOT/'web/src/lib/api.ts').read_text(encoding='utf-8')
HOME=(ROOT/'web/src/app/page.tsx').read_text(encoding='utf-8')
TEMPLATE=ROOT/'templates/livenza_content_studio.html'


def test_content_admin_route_validates_type_json_and_size():
    assert "/admin/livenza/content" in APP
    block=APP.split("/admin/livenza/content",1)[1][:5000]
    assert "@permission_required('content')" in block
    assert 'CONTENT_TYPES' in block
    assert '250 * 1024' in block or '256000' in block
    assert 'json.loads' in block
    assert 'SEO_KEYS' in block


def test_public_content_api_returns_published_only_and_hides_staff_id():
    assert '@api.get("/content/<content_type>/<key>")' in API
    block=API.split('@api.get("/content/<content_type>/<key>")',1)[1][:1800]
    assert "status='published'" in block or 'status == "published"' in block
    assert 'updated_by_user_id' not in block


def test_content_template_exists_with_publish_unpublish_controls():
    assert TEMPLATE.exists()
    text=TEMPLATE.read_text(encoding='utf-8')
    assert 'livenza_content_publish_admin' in text
    assert 'livenza_content_unpublish_admin' in text
    assert 'body_json' in text and 'seo_json' in text


def test_consumer_home_uses_cms_with_safe_fallback():
    assert 'getContent' in WEB_API
    assert 'getContent' in HOME
    assert 'catch' in HOME
    assert 'LIVE MORE.' in HOME
