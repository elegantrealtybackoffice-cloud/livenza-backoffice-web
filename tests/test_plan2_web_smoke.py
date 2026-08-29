from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'


def test_consumer_web_bootstrap_contract():
    package = WEB / 'package.json'
    page = WEB / 'src/app/page.tsx'
    config = WEB / 'next.config.ts'
    assert package.exists(), 'Plan 2 must create web/package.json'
    data = json.loads(package.read_text())
    assert data['dependencies']['next'] == '16.3.3'
    assert data['engines']['node'] == '>=20.9.0'
    assert page.exists()
    assert 'LIVE MORE.' in page.read_text()
    text = config.read_text()
    assert 'LIVENZA_API_ORIGIN' in text
    assert "source: '/api/:path*'" in text
