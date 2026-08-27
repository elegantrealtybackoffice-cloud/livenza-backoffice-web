from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
SHELLJS = (ROOT / 'static/macos27_shell.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/macos27_system.css').read_text(encoding='utf-8')
DOCK_SETTINGS = (ROOT / 'templates/settings/_desktop_dock.html').read_text(encoding='utf-8')


class Hotfix92SettingsDockContracts(unittest.TestCase):
    def test_new_preference_namespace_resets_stale_appearance_without_losing_other_legacy_prefs(self):
        self.assertIn("const PREF_KEY = 'livenza.settings.v2702';", SHELLJS)
        self.assertIn("const PREVIOUS_PREF_KEY = 'livenza.settings.v2701';", SHELLJS)
        self.assertIn("delete legacy['appearance.mode'];", SHELLJS)
        self.assertIn("livenza.settings.v2702", BASE)
        self.assertIn("delete legacy['appearance.mode']", BASE)

    def test_light_mode_explicitly_requests_light_native_controls(self):
        self.assertIn('html[data-appearance="light"]{color-scheme:light}', CSS.replace(' ', ''))

    def test_dock_remains_visible_on_direct_application_routes(self):
        self.assertNotIn('body.macos27-clean:not([data-page="dashboard"]) .mac-dock{display:none}', CSS)
        self.assertIn('id="macDock"', BASE)
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) #appMain\{padding-bottom:calc\(var\(--mac-dock-height\) \+ 36px\)\}')

    def test_dock_magnification_has_scale_and_vertical_lift(self):
        self.assertIn('const DOCK_MAX_LIFT = 13;', SHELLJS)
        self.assertIn("point.item.style.setProperty('--dock-lift'", SHELLJS)
        self.assertIn("item.style.removeProperty('--dock-lift')", SHELLJS)
        compact_css = CSS.replace(' ', '')
        self.assertIn('translateY(calc(-1*var(--dock-lift,0px)))scale(var(--dock-scale))', compact_css)

    def test_disabling_magnification_immediately_clears_active_dock_transform(self):
        self.assertIn("if (pref.dataset.pref === 'dock.magnification') resetDock();", SHELLJS)

    def test_desktop_dock_settings_explain_live_global_behavior(self):
        self.assertIn('Changes apply instantly', DOCK_SETTINGS)
        self.assertIn('every signed-in page', DOCK_SETTINGS)


if __name__ == '__main__':
    unittest.main()
