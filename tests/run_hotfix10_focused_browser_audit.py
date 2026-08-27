from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'static' / 'macos27_system.css').read_text(encoding='utf-8')
JS = str(ROOT / 'static' / 'macos27_shell.js')

HOME = '''<!doctype html><html data-appearance="light"><body data-page="dashboard" class="macos27-clean desktop-widgets-hidden">
<div class="mac-desktop-home">
  <button data-home-widgets-toggle aria-pressed="false">Widgets</button>
  <div id="desktopWallpaperLayer" class="desktop-wallpaper-layer"></div>
  <div id="wallpaperTransitionLayer" class="wallpaper-transition-layer" hidden></div>
  <div id="desktopWindowLayer" class="desktop-window-layer" data-desktop-window-host></div>
  <aside class="home-widget-stack"><section data-home-widget="weather">Weather</section></aside>
</div>
<nav id="macDock" class="mac-dock"><button class="mac-dock-item mac-dock-launcher" data-suites-dock><span class="mac-dock-icon">▦</span></button></nav>
</body></html>'''

SETTINGS = '''<!doctype html><html><head><title>System Settings · Livenza</title></head><body>
<main id="appMain"><div class="system-settings" data-system-settings>
<input id="settingsSearch" type="search"><button id="settingsNavToggle"></button>
<a data-settings-search="Desktop Dock">Desktop & Dock</a>
<input id="autoHide" type="checkbox" data-pref="dock.autohide">
<input id="wallZoom" type="range" min="80" max="160" value="100" data-pref="wallpaper.zoom"><output data-pref-output="wallpaper.zoom">100%</output>
</div></main></body></html>'''


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.set_content(HOME, wait_until='domcontentloaded')
        page.add_style_tag(content=CSS)
        page.add_script_tag(path=JS)
        page.wait_for_timeout(100)

        assert page.locator('body').evaluate("e=>e.classList.contains('desktop-widgets-hidden')") is True
        assert page.locator('html').get_attribute('data-wallpaper') == 'livenza-life'
        wallpaper_bg = page.locator('#desktopWallpaperLayer').evaluate("e=>getComputedStyle(e).backgroundImage")
        assert 'livenza_life_live_elevated.jpg' in wallpaper_bg, wallpaper_bg
        assert page.locator('#macDock .mac-dock-item').count() == 1
        page.screenshot(path=str(ROOT/'tests'/'audit_artifacts'/'hotfix10_clean_home.png'), full_page=False)
        page.locator('[data-home-widgets-toggle]').click()
        assert page.locator('body').evaluate("e=>e.classList.contains('desktop-widgets-hidden')") is False
        page.locator('[data-home-widgets-toggle]').click()
        assert page.locator('body').evaluate("e=>e.classList.contains('desktop-widgets-hidden')") is True
        assert page.locator('html').get_attribute('data-wallpaper') == 'livenza-life'
        wallpaper_bg = page.locator('#desktopWallpaperLayer').evaluate("e=>getComputedStyle(e).backgroundImage")
        assert 'livenza_life_live_elevated.jpg' in wallpaper_bg, wallpaper_bg

        settings_url = 'data:text/html;charset=utf-8,' + quote(SETTINGS)
        page.evaluate("url=>window.LivenzaWindowManager.openAppWindow({endpoint:'settings_page',url,title:'System Settings',tone:'settings',family:'system',accent:'#7c86f8',accent2:'#67707e',iconMarkup:''})", settings_url)
        page.locator('.mac-app-window').wait_for(state='visible', timeout=3000)
        page.locator('#autoHide').wait_for(state='attached', timeout=3000)
        page.locator('#autoHide').check()
        assert page.locator('html').evaluate("e=>e.classList.contains('dock-autohide')") is True

        page.locator('#wallZoom').evaluate("e=>{e.value='125';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        zoom = page.locator('html').evaluate("e=>getComputedStyle(e).getPropertyValue('--wallpaper-zoom').trim()")
        assert zoom == '1.25', zoom

        win = page.locator('.mac-app-window')
        win.locator('.mac-window-titlebar').dblclick(position={'x': 300, 'y': 20})
        assert win.evaluate("e=>e.classList.contains('is-maximized')") is True
        win.locator('.mac-window-titlebar').dblclick(position={'x': 300, 'y': 20})
        assert win.evaluate("e=>e.classList.contains('is-maximized')") is False

        page.screenshot(path=str(ROOT/'tests'/'audit_artifacts'/'hotfix10_desktop_settings.png'), full_page=False)
        browser.close()
    print('Hotfix 10 focused Chromium audit: PASS')

if __name__ == '__main__':
    main()
