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
    def test_dock_renders_only_suites_launcher(self):
        dock = re.search(r'<nav id="macDock"[\s\S]*?</nav>', BASE)
        self.assertIsNotNone(dock)
        markup = dock.group(0)
        self.assertIn('data-suites-dock', markup)
        self.assertNotIn('render_dock_apps()', markup)
        self.assertNotIn('mac-dock-divider', markup)

    def test_widgets_are_closed_by_default_and_opened_from_top_bar(self):
        self.assertIn('data-home-widgets-toggle', DASH)
        self.assertIn('aria-pressed="false"', DASH)
        self.assertIn("'widgets.visible':false", SHELLJS)
        self.assertIn('desktop-widgets-hidden', SHELLJS)
        self.assertRegex(CSS, r'body\.desktop-widgets-hidden \.home-widget-stack\{[^}]*pointer-events:none')

    def test_floating_mascot_is_not_visible_on_home(self):
        self.assertRegex(BASE, r'id="mascotCompanion"[^>]*\shidden(?:\s|>)')
        self.assertIn('data-home-companion-open', DASH)

    def test_widget_settings_describe_on_demand_panel_not_permanent_stack(self):
        self.assertIn('top-bar Widgets control', WIDGET_SETTINGS)
        self.assertNotIn('right-side Home desktop stack', WIDGET_SETTINGS)


if __name__ == '__main__':
    unittest.main()
