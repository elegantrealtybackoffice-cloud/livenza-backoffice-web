from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
DASH = (ROOT / 'templates/dashboard.html').read_text(encoding='utf-8')
WALLPAPER = (ROOT / 'templates/settings/_wallpaper.html').read_text(encoding='utf-8')
SHELLJS = (ROOT / 'static/macos27_shell.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/macos27_system.css').read_text(encoding='utf-8')


class Hotfix10RuntimeContracts(unittest.TestCase):
    def test_settings_initializer_is_idempotent_and_runs_for_window_swaps(self):
        self.assertIn('function initSystemSettings(scope = document)', SHELLJS)
        self.assertIn("settingsRoot.dataset.macosSettingsBound = '1';", SHELLJS)
        self.assertIn("window.addEventListener('livenza:content-swapped'", SHELLJS)
        self.assertIn('initSystemSettings(event.detail?.root || document)', SHELLJS)

    def test_window_loading_has_eight_second_timeout_and_in_window_retry(self):
        self.assertIn('const WINDOW_LOAD_TIMEOUT_MS = 8000;', SHELLJS)
        self.assertIn('const controller = new AbortController();', SHELLJS)
        self.assertIn('WINDOW_LOAD_TIMEOUT_MS', SHELLJS)
        self.assertIn('data-window-retry', SHELLJS)
        self.assertIn('renderWindowLoadError', SHELLJS)

    def test_window_documents_use_memory_cache_and_prefetch(self):
        self.assertIn('const windowDocumentCache = new Map();', SHELLJS)
        self.assertIn('function prefetchWindowDocument', SHELLJS)
        self.assertIn('function fetchWindowDocument', SHELLJS)
        self.assertIn("document.addEventListener('pointerover'", SHELLJS)
        self.assertIn("document.addEventListener('focusin'", SHELLJS)

    def test_wallpaper_has_fit_position_and_zoom_controls(self):
        for token in ('wallpaper.fit', 'wallpaper.positionX', 'wallpaper.positionY', 'wallpaper.zoom'):
            self.assertIn(token, SHELLJS)
        self.assertIn('data-pref="wallpaper.fit"', WALLPAPER)
        self.assertIn('data-pref="wallpaper.positionX"', WALLPAPER)
        self.assertIn('data-pref="wallpaper.positionY"', WALLPAPER)
        self.assertIn('data-pref="wallpaper.zoom"', WALLPAPER)
        self.assertIn('id="desktopWallpaperLayer"', DASH)
        self.assertIn('--wallpaper-zoom', CSS)
        self.assertIn('--wallpaper-position-x', CSS)
        self.assertIn('--wallpaper-position-y', CSS)

    def test_widgets_have_persistent_top_bar_toggle(self):
        self.assertIn('data-home-widgets-toggle', DASH)
        self.assertIn("'widgets.visible':true", SHELLJS)
        self.assertIn('function setWidgetsVisible', SHELLJS)
        self.assertIn("preferences['widgets.visible']", SHELLJS)


    def test_wallpaper_layer_never_intercepts_desktop_controls(self):
        self.assertRegex(CSS, r'\.desktop-wallpaper-layer\{[^}]*pointer-events:none')

    def test_window_titlebar_double_click_toggles_zoom(self):
        self.assertIn("titlebar?.addEventListener('dblclick'", SHELLJS)
        self.assertIn('maximizeAppWindow(windowEl.id)', SHELLJS)

    def test_mascot_markup_is_dashboard_only(self):
        self.assertRegex(BASE, r"\{% if companion_enabled and request\.endpoint == 'dashboard' %\}")

    def test_contextual_window_menu_has_history_commands(self):
        self.assertIn('data-window-menu-command="back-active"', DASH)
        self.assertIn('data-window-menu-command="forward-active"', DASH)
        self.assertIn("name === 'back-active'", SHELLJS)
        self.assertIn("name === 'forward-active'", SHELLJS)


    def test_legacy_compatibility_css_has_balanced_blocks(self):
        legacy = (ROOT / 'static/legacy_modules.css').read_text(encoding='utf-8')
        self.assertEqual(legacy.count('{'), legacy.count('}'))

    def test_route_and_window_loading_errors_are_readable(self):
        self.assertIn('.mac-window-load-error', CSS)
        self.assertIn('.mac-window-retry', CSS)


if __name__ == '__main__':
    unittest.main()
