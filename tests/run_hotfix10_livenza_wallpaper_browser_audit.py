from pathlib import Path
import base64
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'static'/'macos27_system.css').read_text(encoding='utf-8')
JS=str(ROOT/'static'/'macos27_shell.js')
asset=ROOT/'static'/'wallpapers'/'livenza_life_live_elevated_h10l.jpg'
data=base64.b64encode(asset.read_bytes()).decode('ascii')
CSS=CSS.replace('url("wallpapers/livenza_life_live_elevated_h10l.jpg")', f'url("data:image/jpeg;base64,{data}")')
HTML='''<!doctype html><html data-appearance="light"><body data-page="dashboard" class="macos27-clean desktop-widgets-hidden">
<main class="mac-desktop-home"><div id="desktopWallpaperLayer" class="desktop-wallpaper-layer"></div><div id="wallpaperTransitionLayer" class="wallpaper-transition-layer" hidden></div><button data-home-widgets-toggle aria-pressed="false" style="position:fixed;top:8px;right:8px;z-index:50">Widgets</button><div id="desktopWindowLayer" class="desktop-window-layer" data-desktop-window-host></div><aside class="home-widget-stack"><section data-home-widget="weather">Weather</section></aside><nav id="macDock" class="mac-dock"><button class="mac-dock-item mac-dock-launcher" data-suites-dock><span class="mac-dock-icon">▦</span></button></nav></main></body></html>'''
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.set_content(HTML,wait_until='domcontentloaded')
    page.add_style_tag(content=CSS)
    page.add_script_tag(path=JS)
    page.wait_for_timeout(150)
    assert page.locator('html').get_attribute('data-wallpaper')=='livenza-life'
    bg=page.locator('#desktopWallpaperLayer').evaluate("e=>getComputedStyle(e).backgroundImage")
    assert bg.startswith('url("data:image/jpeg;base64,'), bg[:80]
    page.screenshot(path=str(ROOT/'tests'/'audit_artifacts'/'hotfix10_livenza_default_wallpaper.png'),full_page=False)
    browser.close()
print('Hotfix 10 Livenza default wallpaper Chromium audit: PASS')
