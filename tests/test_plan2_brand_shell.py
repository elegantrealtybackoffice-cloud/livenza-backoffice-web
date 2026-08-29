from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_master_shell_exposes_brand_ecosystem_and_booking_action():
    header=(WEB/'src/components/site-header.tsx')
    assert header.exists(), 'site-header.tsx must exist'
    text=header.read_text()
    for label, href in [('Stays','/stays'),('Fit','/fit'),('Store','/store'),('Groom','/groom'),('Skin','/skin'),('Media','/media')]:
        assert label in text and href in text
    assert 'BOOK A STAY' in text and '/stays' in text
    assert 'aria-expanded' in text


def test_brand_tokens_are_locked_and_reduced_motion_is_supported():
    tokens=(WEB/'src/styles/tokens.css')
    brand=(WEB/'src/styles/brand.css')
    assert tokens.exists() and brand.exists()
    t=tokens.read_text(); b=brand.read_text()
    for token in ['--surface:', '--ink:', '--brand-accent:', '--radius-md:', '--motion-standard:']:
        assert token in t
    for selector,color in [
        ('[data-brand="stays"]','#155ed6'),('[data-brand="store"]','#dd641c'),
        ('[data-brand="fit"]','#a6cf24'),('[data-brand="groom"]','#6f1734'),
        ('[data-brand="skin"]','#e98278'),('[data-brand="media"]','#00a9c7')]:
        assert selector in b and color in b.lower()
    assert 'prefers-reduced-motion' in t
