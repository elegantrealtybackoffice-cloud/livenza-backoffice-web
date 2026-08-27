from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
DASH = (ROOT / 'templates/dashboard.html').read_text(encoding='utf-8')
SHELLJS = (ROOT / 'static/macos27_shell.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/macos27_system.css').read_text(encoding='utf-8')
WIDGET_SETTINGS = (ROOT / 'templates/settings/_widgets.html').read_text(encoding='utf-8')


class Hotfix10CleanHomeContracts(unittest.TestCase):
    def test_dock_renders_curated_lightweight_launchers(self):
        dock = re.search(r'<nav id="macDock"[\s\S]*?</nav>', BASE)
        self.assertIsNotNone(dock)
        markup = dock.group(0)
        self.assertIn('data-suites-dock', markup)
        for endpoint in ('agreements','rooms','queries','reviews','banking_suite','settings_page'):
            self.assertIn(f'data-dock-app="{endpoint}"', markup)
        self.assertNotIn('render_dock_apps()', markup)

    def test_widgets_are_closed_by_default_and_opened_from_top_bar(self):
        self.assertIn('data-home-widgets-toggle', DASH)
        self.assertIn('aria-pressed="false"', DASH)
        self.assertIn("'widgets.visible':false", SHELLJS)
        self.assertIn('desktop-widgets-hidden', SHELLJS)
        self.assertRegex(CSS, r'body\.desktop-widgets-hidden \.home-widget-stack\{[^}]*pointer-events:none')

    def test_compact_mascot_is_dock_adjacent_and_lazy(self):
        self.assertNotIn('id="mascotCompanion"', BASE)
        self.assertIn('home-companion-launcher', DASH)
        self.assertIn('home-companion-panel', DASH)
        self.assertIn('data-home-companion-open', DASH)

    def test_widget_settings_describe_on_demand_panel_not_permanent_stack(self):
        self.assertIn('top-bar Widgets control', WIDGET_SETTINGS)
        self.assertNotIn('right-side Home desktop stack', WIDGET_SETTINGS)


if __name__ == '__main__':
    unittest.main()
