from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'static/home_light.js').read_text(encoding='utf-8').replace(' ', '')

class Hotfix10PartialDeployNavigation(unittest.TestCase):
    def test_suites_handler_binds_only_when_drawer_exists(self):
        self.assertIn("if(drawer){$$('[data-suites-dock]').forEach", JS)

    def test_menu_handler_falls_back_when_popover_missing(self):
        self.assertIn("if(!menu)return;e.preventDefault();e.stopPropagation()", JS)

    def test_widgets_handler_binds_only_when_widget_stack_exists(self):
        self.assertIn("if(widgetStack){$$('[data-home-widgets-toggle]').forEach", JS)

    def test_companion_handler_binds_only_when_panel_exists(self):
        self.assertIn("if(companion){$$('[data-home-companion-open]').forEach", JS)

    def test_search_handler_binds_only_when_palette_exists(self):
        self.assertIn("if(palette){$$('[data-mac-command-open]').forEach", JS)

if __name__ == '__main__':
    unittest.main()
