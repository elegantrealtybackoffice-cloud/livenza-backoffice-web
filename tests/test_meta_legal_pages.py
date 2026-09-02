from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'


def _text(rel: str) -> str:
    path = WEB / rel
    assert path.exists(), f'missing {rel}'
    return path.read_text(encoding='utf-8')


def test_meta_legal_routes_exist_with_canonical_metadata_and_required_content():
    expectations = {
        'privacy': ['Privacy Policy', 'WhatsApp', 'OTP', 'info@livenzalife.com'],
        'terms': ['Terms of Service', 'booking', 'refund', 'India', 'info@livenzalife.com'],
        'data-deletion': ['Data Deletion', 'Data Deletion Request', 'OTP', 'info@livenzalife.com'],
    }
    for route, required in expectations.items():
        text = _text(f'src/app/{route}/page.tsx')
        assert "from '../legal.module.css'" in text
        assert f"https://livenza.life/{route}" in text
        for token in required:
            assert token.lower() in text.lower(), f'{token!r} missing from /{route}'


def test_shared_legal_css_module_is_responsive_and_readable():
    legal_css = _text('src/app/legal.module.css')
    for token in ['.page', '.hero', '.section', '.list', '@media']:
        assert token in legal_css
