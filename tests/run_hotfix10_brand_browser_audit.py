from pathlib import Path
import base64
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
LEGACY=(ROOT/'static'/'legacy_modules.css').read_text(encoding='utf-8')
CSS=(ROOT/'static'/'macos27_system.css').read_text(encoding='utf-8')
OUT=ROOT/'tests'/'audit_artifacts'
OUT.mkdir(parents=True, exist_ok=True)

def data_uri(name):
    raw=(ROOT/'static'/'brand'/name).read_bytes()
    return 'data:image/png;base64,'+base64.b64encode(raw).decode('ascii')

WORD=data_uri('livenza_wordmark.png')
WORD_DARK=data_uri('livenza_wordmark_on_dark.png')
TAG=data_uri('livenza_wordmark_tagline.png')
MARK_DARK=data_uri('livenza_life_mark_on_dark.png')

HTML=f'''<!doctype html><html data-appearance="light" data-wallpaper="aurora"><head><meta charset="utf-8"></head>
<body class="macos27-clean" data-page="dashboard">
<section class="mac-desktop-home" style="position:relative;height:190px;overflow:hidden">
<nav class="mac-desktop-menubar" style="position:absolute"><div class="desktop-menu-left"><a class="desktop-menu-logo"><img id="menuBrand" src="{WORD_DARK}"></a><strong class="desktop-active-app">Livenza Life</strong><button class="desktop-menu-command">Suites</button></div><div class="desktop-menu-right"><span class="desktop-menu-time">10:09</span></div></nav>
<div class="desktop-wallpaper-layer"></div></section>
<main style="padding:32px;display:grid;gap:28px;background:#f5f8fb">
<section class="login-card auth-login-card biometric-first-login" style="margin:0 auto"><img id="loginBrand" src="{TAG}" class="login-logo"><p class="eyebrow">SECURE WEB ACCESS</p><h1>Welcome to Livenza</h1><p class="muted">Device-native authentication</p><button class="primary biometric-primary">Verify Device</button></section>
<section class="agreement-brand-banner liquid-card"><div class="agreement-brand-mark"><img id="agreementBrand" src="{WORD}"><i></i><i></i><i></i></div><div><p class="eyebrow">FORMAL OPERATIONS WORKSPACE</p><h2>Agreements shaped for Livenza Life</h2><p>Secure formal document workflow</p></div><div class="agreement-trust-badge"><span>✓</span><div><b>Protected workspace</b><small>Secure session</small></div></div></section>
<section class="letterhead-paper" style="width:min(760px,100%);min-height:360px;margin:auto"><img id="letterBrand" class="letterhead-brand-logo" src="{TAG}"><div class="letterhead-paper-brand">Livenza Life LLP</div><h3>Sample Official Letter</h3><p>Brand system preview.</p></section>
<section style="background:#061a3a;padding:24px;border-radius:20px;display:grid;place-items:center"><img id="markDark" src="{MARK_DARK}" style="width:108px;height:108px;object-fit:contain"></section>
</main></body></html>'''

def assert_layout(page, mobile=False):
    for selector in ('#menuBrand','#loginBrand','#agreementBrand','#letterBrand','#markDark'):
        assert page.locator(selector).evaluate('e=>e.complete && e.naturalWidth>0'), selector
    menu=page.locator('#menuBrand').bounding_box(); assert menu and menu['height'] <= 24 and menu['width'] <= 100, menu
    login=page.locator('#loginBrand').bounding_box(); card=page.locator('.auth-login-card').bounding_box(); assert login and card and login['width'] <= card['width']-20, (login,card)
    agreement=page.locator('.agreement-brand-banner').bounding_box(); brand=page.locator('#agreementBrand').bounding_box(); assert agreement and brand and brand['width'] <= agreement['width'], (agreement,brand)
    letter=page.locator('.letterhead-paper').bounding_box(); lbrand=page.locator('#letterBrand').bounding_box(); assert letter and lbrand and lbrand['width'] <= letter['width']*.7, (letter,lbrand)
    overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth'); assert overflow <= 1, overflow
    if mobile:
        cols=page.locator('.agreement-brand-banner').evaluate("e=>getComputedStyle(e).gridTemplateColumns")
        assert cols.count(' ') < 2, cols


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        for width,height,name,mobile in [(1440,1000,'hotfix10_brand_desktop.png',False),(390,844,'hotfix10_brand_mobile.png',True)]:
            page=browser.new_page(viewport={'width':width,'height':height})
            page.set_content(HTML,wait_until='load')
            page.add_style_tag(content=LEGACY)
            page.add_style_tag(content=CSS)
            page.wait_for_timeout(150)
            assert_layout(page,mobile)
            page.screenshot(path=str(OUT/name),full_page=True)
            page.close()
        browser.close()
    print('Hotfix 10 brand Chromium audit: PASS (desktop + mobile)')

if __name__=='__main__':
    main()
