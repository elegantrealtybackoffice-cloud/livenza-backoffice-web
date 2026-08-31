from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
SHELL = (ROOT / 'static/macos27_shell.js').read_text(encoding='utf-8')
STAFF_CSS = (ROOT / 'static/staff_salary.css').read_text(encoding='utf-8')


class UiPerformanceHardeningTests(unittest.TestCase):
    def test_shared_ui_integrity_stylesheet_loads_last_on_app_routes(self):
        path = ROOT / 'static/ui_integrity.css'
        self.assertTrue(path.exists(), 'shared UI integrity stylesheet must exist')
        self.assertIn("filename='ui_integrity.css'", BASE)
        self.assertGreater(BASE.index("filename='ui_integrity.css'"), BASE.index("filename='staff_salary.css'"))

    def test_staff_salary_surfaces_follow_theme_tokens(self):
        css = (ROOT / 'static/ui_integrity.css').read_text(encoding='utf-8')
        for token in ('.staff-card', '.staff-kpis article', 'var(--mac-label)', 'var(--mac-surface-strong)'):
            self.assertIn(token, css)
        self.assertRegex(css, r'data-appearance="dark"[\s\S]*\.staff-card')

    def test_shared_integrity_layer_has_readable_forms_and_safe_layout(self):
        css = (ROOT / 'static/ui_integrity.css').read_text(encoding='utf-8')
        self.assertIn(':is(input,select,textarea)', css)
        self.assertIn('overflow-wrap:anywhere', css)
        self.assertIn('min-width:0', css)
        self.assertIn('scroll-margin-top', css)

    def test_setting_reads_use_short_ttl_cache_and_writes_invalidate(self):
        self.assertIn('SETTING_CACHE_TTL_SECONDS', APP)
        self.assertIn('_SETTING_CACHE', APP)
        setting_block = APP[APP.index('def setting('):APP.index('def set_setting(')]
        self.assertIn('time.monotonic()', setting_block)
        set_block = APP[APP.index('def set_setting('):APP.index('GOOGLE_SCOPES')]
        self.assertIn('_SETTING_CACHE.pop', set_block)

    def test_missing_setting_cache_preserves_each_callers_default(self):
        self.assertIn('_SETTING_MISSING', APP)
        setting_block = APP[APP.index('def setting('):APP.index('def set_setting(')]
        self.assertIn('cached[0] is _SETTING_MISSING', setting_block)
        self.assertIn('_SETTING_MISSING if row is None else row.value', setting_block)

    def test_partial_window_requests_use_lightweight_context(self):
        self.assertIn("request.headers.get('X-Livenza-Partial') == '1'", APP)
        block = APP[APP.index("request.headers.get('X-Livenza-Partial') == '1'"):APP.index("if request.endpoint == 'dashboard':")]
        self.assertIn('dock_apps=lightweight_dock_apps(user)', block)
        self.assertNotIn('mascot_preferences_for(', block)
        self.assertNotIn('visible_dock_apps(', block)

    def test_partial_window_markup_skips_duplicate_shell_chrome(self):
        self.assertIn('partial_window_request', BASE)
        self.assertRegex(BASE, r'if not partial_window_request[\s\S]*macDock')
        self.assertRegex(BASE, r'if not partial_window_request[\s\S]*macCommandPalette')

    def test_visible_dock_build_is_single_pass(self):
        block = APP[APP.index('def visible_dock_apps('):APP.index('def lightweight_dock_apps(')]
        self.assertIn('route_names=', block)
        self.assertIn('permissions=', block)
        self.assertIn('google_ready=', block)
        self.assertNotIn('ui_app_available(', block)

    def test_window_document_cache_is_long_enough_for_tab_switching(self):
        match = re.search(r'WINDOW_CACHE_TTL_MS\s*=\s*([0-9_]+)', SHELL)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1).replace('_','')), 120_000)

    def test_hover_prefetch_is_debounced_to_avoid_request_storms(self):
        self.assertIn('PREFETCH_DELAY_MS', SHELL)
        self.assertIn('prefetchTimer', SHELL)
        self.assertRegex(SHELL, r'setTimeout\(\(\) => prefetchWindowDocument')


if __name__ == '__main__':
    unittest.main()
