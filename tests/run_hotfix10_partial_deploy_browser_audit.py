from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = str(ROOT / 'static/home_light.js')
HTML = '''<!doctype html><html><body class="desktop-widgets-hidden">
<a id="suites" href="#suites" data-suites-dock>Suites</a>
<a id="view" href="#view" data-window-menu-trigger="view">View</a>
<a id="window" href="#window" data-window-menu-trigger="window">Window</a>
<a id="help" href="#help" data-home-companion-open>Help</a>
<a id="widgets" href="#widgets" data-home-widgets-toggle>Widgets</a>
<a id="search" href="#search" data-mac-command-open>Search</a>
<time id="homeCurrentDate"></time><time id="homeCurrentTime"></time>
</body></html>'''

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    page.set_content(HTML)
    page.add_script_tag(path=JS)
    for element_id in ('suites','view','window','help','widgets','search'):
        result = page.eval_on_selector(f'#{element_id}', '''el => {
          const ev = new MouseEvent('click',{bubbles:true,cancelable:true});
          el.dispatchEvent(ev);
          return ev.defaultPrevented;
        }''')
        assert result is False, f'{element_id} fallback click was canceled by Home JS'
    browser.close()
print('Hotfix 10 partial-deploy browser audit: PASS')
