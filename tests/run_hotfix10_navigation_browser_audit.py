from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'static/home_light.css').read_text(encoding='utf-8')
JS=str(ROOT/'static/home_light.js')
HTML='''<!doctype html><html><body class="desktop-widgets-hidden"><div id="appViewport"><section class="mac-desktop-home">
<nav class="mac-desktop-menubar"><div class="desktop-menu-left">
<a class="desktop-menu-command" href="?suites=1" data-suites-dock>Suites</a>
<a class="desktop-menu-command" href="#appearance" data-window-menu-trigger="view">View</a>
<a class="desktop-menu-command" href="#settings" data-window-menu-trigger="window">Window</a>
<a class="desktop-menu-command" href="#help" data-home-companion-open>Help</a></div><div class="desktop-menu-right">
<a class="desktop-status-button" href="#widgets" data-home-widgets-toggle>W</a><a class="desktop-status-button" href="?suites=1" data-mac-command-open>S</a><time id="homeCurrentDate"></time><time id="homeCurrentTime"></time></div></nav>
<div class="desktop-menu-popover" data-window-menu="view" hidden><button data-home-command="toggle-widgets">Toggle Widgets</button></div>
<div class="desktop-menu-popover" data-window-menu="window" hidden><a href="#settings">Settings</a></div>
<div class="desktop-wallpaper-layer"></div><aside class="home-widget-stack"><section class="home-widget">Widgets</section></aside>
<a class="home-companion-launcher" href="#help" data-home-companion-open>H</a><aside class="home-companion-panel" hidden><button data-home-companion-close>x</button>Help</aside>
</section></div>
<div id="appsMenuBackdrop" class="apps-drawer-backdrop" hidden></div><nav id="appsDrawer" class="apps-drawer" hidden><button data-drawer-close>x</button><a class="light-suite-card" href="#agreement">Agreement</a></nav>
<nav id="macDock" class="mac-dock"><a class="mac-dock-item mac-dock-launcher" href="?suites=1" data-suites-dock><span class="mac-dock-icon">S</span></a><a class="mac-dock-item dock-agreement" href="#agreement" data-dock-app="agreements"><span class="mac-dock-icon">A</span></a><a class="mac-dock-item dock-settings" href="#settings" data-dock-app="settings_page"><span class="mac-dock-icon">G</span></a></nav>
<div id="macCommandPalette" class="mac-command-backdrop" hidden><input id="macGlobalSearch"><button id="macCommandClose">x</button><a data-command-item data-command-label="Agreement">Agreement</a></div>
</body></html>'''

def assert_topmost(page, selector):
    loc=page.locator(selector).first
    box=loc.bounding_box(); assert box, selector
    x=box['x']+box['width']/2; y=box['y']+box['height']/2
    ok=page.evaluate("""([x,y,sel])=>{const target=document.querySelector(sel);const hit=document.elementFromPoint(x,y);return !!hit && (hit===target || target.contains(hit));}""", [x,y,selector])
    assert ok, f'click target blocked: {selector}'


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':900})
        # No-JS: every essential visible control must remain a real, unobstructed link.
        page.set_content(HTML,wait_until='domcontentloaded'); page.add_style_tag(content=CSS)
        for sel in ['[data-suites-dock]','[data-window-menu-trigger="view"]','[data-window-menu-trigger="window"]','[data-home-companion-open]','[data-home-widgets-toggle]','[data-mac-command-open]','[data-dock-app="agreements"]','[data-dock-app="settings_page"]']:
            assert page.locator(sel).first.get_attribute('href'), sel
            assert_topmost(page,sel)
        page.locator('[data-dock-app="agreements"]').click(); assert page.evaluate('location.hash')=='#agreement'

        # JS-enhanced: controls open panels locally and do not follow fallbacks.
        page.set_content(HTML,wait_until='domcontentloaded'); page.add_style_tag(content=CSS); page.add_script_tag(path=JS)
        page.locator('[data-suites-dock]').first.click(); assert page.locator('#appsDrawer').is_visible(); assert not page.url.endswith('?suites=1')
        page.locator('[data-drawer-close]').click(); assert not page.locator('#appsDrawer').is_visible()
        page.locator('[data-window-menu-trigger="view"]').click(); assert page.locator('[data-window-menu="view"]').is_visible(); assert page.evaluate('location.hash')!='#appearance'
        page.locator('[data-home-widgets-toggle]').click(); assert not page.locator('body').evaluate("e=>e.classList.contains('desktop-widgets-hidden')"); assert page.evaluate('location.hash')!='#widgets'
        page.locator('[data-home-companion-open]').first.click(); assert page.locator('.home-companion-panel').is_visible(); assert page.evaluate('location.hash')!='#help'
        page.locator('[data-mac-command-open]').click(); assert page.locator('#macCommandPalette').is_visible(); assert not page.url.endswith('?suites=1')
        assert page.evaluate("document.documentElement.dataset.homeRuntime")=='ready'
        browser.close()
    print('Hotfix 10 navigation browser audit: PASS (no-JS + enhanced)')

if __name__=='__main__': main()
