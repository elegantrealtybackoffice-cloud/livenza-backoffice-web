from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
DASH = (ROOT / 'templates/dashboard.html').read_text(encoding='utf-8')
JS = (ROOT / 'static/home_light.js').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')

class Hotfix10NavigationResilience(unittest.TestCase):
    def test_suites_controls_have_real_no_js_href(self):
        # Both menu and Dock Suites controls must be anchors to a server-rendered fallback.
        controls = re.findall(r'<(?:a|button)[^>]*data-suites-dock[^>]*>', BASE + DASH)
        self.assertGreaterEqual(len(controls), 2)
        for tag in controls:
            self.assertTrue(tag.startswith('<a '), tag)
            self.assertIn("url_for('dashboard',suites=1)", tag.replace(' ', ''), tag)

    def test_server_can_render_suites_drawer_open_from_query_flag(self):
        self.assertIn("request.args.get('suites') == '1'", BASE)
        self.assertRegex(BASE, r'id="appsDrawer"[\s\S]{0,300}suites_fallback_open')

    def test_dock_applications_are_real_links_not_js_buttons(self):
        dock = re.search(r'<nav id="macDock"[\s\S]*?</nav>', BASE)
        self.assertIsNotNone(dock)
        markup = dock.group(0)
        for endpoint in ('agreements','rooms','queries','reviews','banking_suite','settings_page'):
            match = re.search(rf'<a[^>]+data-dock-app="{endpoint}"[^>]+href="\{{\{{url_for\(', markup)
            self.assertIsNotNone(match, endpoint)

    def test_js_only_enhances_suites_fallback(self):
        self.assertIn("e.preventDefault();setDrawer", JS.replace(' ', ''))

    def test_navigation_release_uses_new_revision(self):
        self.assertIn("27A101-H10L-20260827E", APP)

    def test_top_bar_controls_have_no_js_navigation_fallbacks(self):
        required = {
            'data-window-menu-trigger="view"': "system_settings_pane',pane='appearance",
            'data-window-menu-trigger="window"': "settings_page",
            'data-home-companion-open': "system_settings_pane',pane='intelligence",
            'data-home-widgets-toggle': "system_settings_pane',pane='widgets",
            'data-mac-command-open': "dashboard',suites=1",
        }
        for marker, target in required.items():
            tag = re.search(rf'<(?:a|button)[^>]*{re.escape(marker)}[^>]*>', DASH)
            self.assertIsNotNone(tag, marker)
            self.assertTrue(tag.group(0).startswith('<a '), tag.group(0))
            self.assertIn('href=', tag.group(0))
            self.assertIn(target, tag.group(0).replace(' ', ''))

    def test_js_prevents_fallback_navigation_when_enhancement_is_alive(self):
        compact = JS.replace(' ', '')
        self.assertIn("[data-window-menu-trigger]", compact)
        self.assertIn('e.preventDefault();e.stopPropagation()', compact)
        self.assertIn("[data-home-companion-open]", compact)
        self.assertIn('e.preventDefault();setCompanion', compact)
        self.assertIn("[data-home-widgets-toggle]", compact)
        self.assertIn('e.preventDefault();setWidgets', compact)

if __name__ == '__main__':
    unittest.main()
