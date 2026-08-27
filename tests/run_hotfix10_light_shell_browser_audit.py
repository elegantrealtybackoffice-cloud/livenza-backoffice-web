from pathlib import Path
import base64
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HOME_CSS=(ROOT/'static/home_light.css').read_text(encoding='utf-8')
HOME_JS=str(ROOT/'static/home_light.js')
SETTINGS_CSS=(ROOT/'static/settings_light.css').read_text(encoding='utf-8')
WALL=(ROOT/'static/wallpapers/livenza_life_live_elevated_h10l.jpg').read_bytes()
WALL_URI='data:image/jpeg;base64,'+base64.b64encode(WALL).decode('ascii')
ICON='<svg class="lz-symbol" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="5" y="5" width="14" height="14" rx="3"/><path d="M9 9h6M9 12h6M9 15h6"/></svg>'

HOME=f'''<!doctype html><html data-wallpaper="livenza-life" data-wallpaper-fit="fill"><body data-page="dashboard" data-build-revision="27A101-H10L-20260827B" class="app-liquid-shell macos27-clean desktop-widgets-hidden">
<div id="appViewport"><div id="macShell" class="mac-shell"><div class="mac-shell-body"><section class="mac-workspace"><main id="appMain"><section class="mac-desktop-home">
<nav class="mac-desktop-menubar"><div class="desktop-menu-left"><a class="desktop-menu-logo"><span>L</span></a><strong class="desktop-active-app">Livenza Life</strong><button class="desktop-menu-command" data-suites-dock>Suites</button><button class="desktop-menu-command" data-window-menu-trigger="view">View</button><button class="desktop-menu-command" data-window-menu-trigger="window">Window</button><button class="desktop-menu-command" data-home-companion-open>Help</button></div><div class="desktop-menu-right"><button class="desktop-status-button" data-home-widgets-toggle>W</button><button class="desktop-status-button" data-mac-command-open>S</button><time id="homeCurrentDate"></time><time id="homeCurrentTime"></time></div></nav>
<div class="desktop-menu-popover" data-window-menu="view" hidden><button data-home-command="toggle-widgets">Toggle Widgets</button><button data-home-command="fullscreen">Full Screen</button></div><div class="desktop-menu-popover" data-window-menu="window" hidden><a>System Settings</a><button data-suites-dock>Open Suites</button></div>
<div id="desktopWallpaperLayer" class="desktop-wallpaper-layer"></div><div id="wallpaperTransitionLayer"></div><div class="home-wallpaper-sheen"></div><div id="desktopWindowLayer"></div>
<aside class="home-widget-stack"><section class="home-widget"><header><b>Quick Actions</b><small>On demand</small></header><div class="home-widget-links"><a>Agreement</a><a>Queries</a><a>Rooms</a><a>Settings</a></div></section><section class="home-widget"><header><b>Hotfix 10 Light Shell</b><small>27A101-H10L</small></header><small>No weather polling or application prefetch runs on Home.</small></section></aside>
<button class="home-companion-launcher" data-home-companion-open><img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="></button><aside class="home-companion-panel" hidden><header><b>Livenza Companion</b><button data-home-companion-close>×</button></header><p>Quick help</p><span class="home-build-chip">27A101-H10L</span></aside>
</section></main></section></div></div>
<div id="appsMenuBackdrop" class="apps-drawer-backdrop" hidden></div><nav id="appsDrawer" class="apps-drawer" hidden><div class="apps-drawer-head"><div><b>Suites</b></div><button data-drawer-close>×</button></div><div class="apps-drawer-scroll"><div class="light-suite-grid"><a class="light-suite-card"><i>{ICON}</i><b>System Settings</b></a><a class="light-suite-card"><i>{ICON}</i><b>Agreement Studio</b></a><a class="light-suite-card"><i>{ICON}</i><b>Rooms</b></a><a class="light-suite-card"><i>{ICON}</i><b>Queries</b></a></div></div></nav>
<nav id="macDock" class="mac-dock">'''+''.join([f'<a class="mac-dock-item mac-dock-app dock-{name}" data-dock-app="{name}"><span class="mac-dock-icon">{ICON}</span><span class="mac-dock-tooltip">{name}</span><i class="mac-dock-running"></i></a>' for name in ['launcher','agreement','rooms','queries','reviews','banking','settings']])+'''</nav>
<div id="macCommandPalette" class="mac-command-backdrop" hidden><section class="mac-command-palette"><div class="mac-command-search-wrap">S<input id="macGlobalSearch"><button id="macCommandClose">×</button></div><div class="mac-command-results"><a class="mac-command-item" data-command-item data-command-label="Settings" data-command-keywords="appearance dock"><span>S</span><span><b>Settings</b><small>Appearance</small></span><kbd>↵</kbd></a></div></section></div>
</div></body></html>'''

SETTINGS='''<!doctype html><html><body><header class="mac-toolbar"><div class="mac-route-window-controls"><i class="mac-window-control close"></i><i class="mac-window-control minimize"></i><i class="mac-window-control maximize"></i></div><div class="mac-route-window-title-identity"><span class="mac-window-mini-icon">⚙</span><strong class="mac-window-title">System Settings</strong></div><div class="mac-route-window-actions"><button>↻</button></div></header><main class="app-content-shell"><div class="system-settings"><aside class="system-settings-sidebar"><div class="settings-profile-card"><span class="settings-avatar-fallback">R</span><span><b>Livenza User</b><small>Admin · Livenza Life</small></span></div><label class="settings-search"><span>⌕</span><input placeholder="Search Settings"><kbd>⌘F</kbd></label><p class="settings-nav-group">System</p><a class="settings-nav-row active"><span class="settings-nav-icon">◐</span><span><b>Appearance</b><small>Wallpaper, contrast and interface</small></span><span>›</span></a><a class="settings-nav-row"><span class="settings-nav-icon">▤</span><span><b>Desktop & Dock</b><small>Dock size and magnification</small></span><span>›</span></a></aside><section class="system-settings-detail"><header class="settings-detail-header"><span class="settings-detail-icon">◐</span><div><p class="eyebrow">SYSTEM SETTINGS</p><h1>Appearance</h1><p>Bright, fast and readable Livenza controls.</p></div></header><section class="settings-card" style="padding:18px"><h3>Appearance</h3><p>Light interface</p><label>Dock size <input type="range"></label></section></section></div></main><nav class="mac-dock"><a class="mac-dock-item dock-settings"><span class="mac-dock-icon">⚙</span></a></nav></body></html>'''

def audit_home(page,width,height,name):
    page.set_viewport_size({'width':width,'height':height})
    page.set_content(HOME,wait_until='domcontentloaded')
    page.add_style_tag(content=HOME_CSS+f"\n.desktop-wallpaper-layer{{background-image:url('{WALL_URI}')!important}}")
    page.add_script_tag(path=HOME_JS)
    assert page.locator('#macDock .mac-dock-item').count()==7
    assert page.locator('body').evaluate("e=>e.classList.contains('desktop-widgets-hidden')") is True
    elapsed=page.evaluate("""()=>{const b=document.querySelector('[data-window-menu-trigger="view"]');const t=performance.now();b.click();return performance.now()-t} """)
    assert elapsed < 25, elapsed
    assert page.locator('[data-window-menu="view"]').is_visible()
    page.locator('[data-home-widgets-toggle]').click()
    assert page.locator('body').evaluate("e=>e.classList.contains('desktop-widgets-hidden')") is False
    page.locator('[data-home-widgets-toggle]').click()
    launcher=page.locator('.home-companion-launcher').bounding_box();dock=page.locator('#macDock').bounding_box()
    assert launcher and dock
    assert width-(launcher['x']+launcher['width']) < 45
    assert launcher['y']+launcher['height'] <= dock['y']+5
    page.locator('[data-home-companion-open]').last.click()
    assert page.locator('.home-companion-panel').is_visible()
    overflow=page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
    assert overflow <= 1, overflow
    out=ROOT/'tests'/'audit_artifacts'/name
    page.screenshot(path=str(out),full_page=False)


def main():
    outdir=ROOT/'tests'/'audit_artifacts';outdir.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page()
        audit_home(page,1920,1080,'hotfix10_light_home_desktop.png')
        audit_home(page,1366,768,'hotfix10_light_home_laptop.png')
        page.set_viewport_size({'width':1440,'height':900});page.set_content(SETTINGS,wait_until='domcontentloaded');page.add_style_tag(content=SETTINGS_CSS)
        bg=page.locator('.system-settings-detail').evaluate("e=>getComputedStyle(e).backgroundColor")
        assert bg in ('rgb(255, 255, 255)','rgba(255, 255, 255, 1)'),bg
        assert page.locator('.system-settings-sidebar').bounding_box()['width'] >= 285
        overflow=page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth");assert overflow<=1,overflow
        page.screenshot(path=str(outdir/'hotfix10_light_settings.png'),full_page=False)
        browser.close()
    print('Hotfix 10 light shell Chromium audit: PASS')

if __name__=='__main__':main()
