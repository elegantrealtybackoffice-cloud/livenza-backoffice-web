from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
DASH = (ROOT / 'templates/dashboard.html').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
HOME_CSS_PATH = ROOT / 'static/home_light.css'
HOME_JS_PATH = ROOT / 'static/home_light.js'
SETTINGS_CSS_PATH = ROOT / 'static/settings_light.css'


class Hotfix10LightShellContracts(unittest.TestCase):
    def test_dashboard_uses_dedicated_light_assets_only(self):
        self.assertIn("lightweight_home_route", BASE)
        self.assertIn("filename='home_light.css'", BASE)
        self.assertIn("filename='home_light.js'", BASE)
        # Heavy application bundles must be behind the non-dashboard branch.
        dashboard_branch = BASE.split("{% if lightweight_home_route %}",1)[1].split('{% elif lightweight_settings_route %}',1)[0]
        self.assertNotIn("filename='legacy_modules.css'", dashboard_branch)
        self.assertNotIn("filename='app.js'", dashboard_branch)
        self.assertIn("filename='legacy_modules.css'", BASE)
        self.assertIn("filename='app.js'", BASE)

    def test_settings_routes_avoid_legacy_and_tv_runtime(self):
        self.assertIn("lightweight_settings_route", BASE)
        self.assertIn("filename='settings_light.css'", BASE)
        self.assertRegex(BASE, r"if not lightweight_settings_route[\s\S]*filename='legacy_modules\.css'")
        self.assertRegex(BASE, r"if not lightweight_settings_route[\s\S]*filename='tv_compat\.js'")
        self.assertRegex(BASE, r"if not lightweight_settings_route[\s\S]*filename='app\.js'")

    def test_light_home_assets_exist_and_stay_small(self):
        self.assertTrue(HOME_CSS_PATH.exists())
        self.assertTrue(HOME_JS_PATH.exists())
        self.assertLess(HOME_CSS_PATH.stat().st_size, 45000)
        self.assertLess(HOME_JS_PATH.stat().st_size, 30000)
        css = HOME_CSS_PATH.read_text(encoding='utf-8')
        js = HOME_JS_PATH.read_text(encoding='utf-8')
        self.assertNotIn('backdrop-filter:blur(100px)', css.replace(' ', ''))
        self.assertNotIn('/api/companion/pulse', js)
        self.assertNotIn('pointerover', js)

    def test_home_dock_has_curated_professional_apps(self):
        dock = re.search(r'<nav id="macDock"[\s\S]*?</nav>', BASE)
        self.assertIsNotNone(dock)
        markup = dock.group(0)
        for label in ('Suites','Agreement Studio','Rooms','Queries','Reviews','Banking','System Settings'):
            self.assertIn(label, markup)
        self.assertGreaterEqual(markup.count('mac-dock-item'), 7)
        self.assertIn('data-dock-app="agreements"', markup)
        self.assertIn('data-dock-app="settings_page"', markup)

    def test_companion_is_compact_and_lazy_on_home(self):
        self.assertIn('home-companion-launcher', DASH)
        self.assertIn('home-companion-panel', DASH)
        self.assertNotIn('homeWeatherTemperature', DASH)
        self.assertNotIn('companionForecast', DASH)
        self.assertNotIn('livenzaWeatherScene', DASH)

    def test_dashboard_context_avoids_settings_and_mascot_queries(self):
        self.assertIn("if request.endpoint == 'dashboard':", APP)
        branch = APP.split("if request.endpoint == 'dashboard':",1)[1].split('user=current_user()',1)[0]
        self.assertNotIn('setting(', branch)
        self.assertNotIn('mascot_preferences_for(', branch)
        self.assertNotIn('visible_dock_apps(', branch)

    def test_deployment_revision_is_visible_in_version_and_headers(self):
        self.assertRegex(APP, r"ASSET_REVISION\s*=\s*'[^']*H10L[^']*'")
        self.assertIn("revision=ASSET_REVISION", APP)
        self.assertIn("response.headers['X-Livenza-Revision'] = ASSET_REVISION", APP)
        self.assertIn('asset_revision=ASSET_REVISION', APP)
        self.assertIn('?rev={{asset_revision}}', BASE)


    def test_all_versioned_static_assets_use_hotfix_revision_not_os_version(self):
        for template in (ROOT / 'templates').rglob('*.html'):
            text = template.read_text(encoding='utf-8')
            self.assertNotIn("?v={{app_version", text, str(template))

    def test_settings_light_css_exists_and_avoids_heavy_glass(self):
        self.assertTrue(SETTINGS_CSS_PATH.exists())
        css = SETTINGS_CSS_PATH.read_text(encoding='utf-8')
        self.assertLess(SETTINGS_CSS_PATH.stat().st_size, 30000)
        self.assertIn('.system-settings', css)
        self.assertNotIn('blur(100px)', css)

    def test_default_wallpaper_uses_unique_hotfix_asset_path(self):
        home_css = HOME_CSS_PATH.read_text(encoding='utf-8')
        self.assertIn('livenza_life_live_elevated_h10l.jpg', home_css)
        self.assertTrue((ROOT / 'static/wallpapers/livenza_life_live_elevated_h10l.jpg').exists())

    def test_settings_forms_and_switch_rows_have_explicit_layout(self):
        css = SETTINGS_CSS_PATH.read_text(encoding='utf-8')
        for selector in ('.form-grid','.settings-toggle-row','.settings-toggle-list','.mac-switch','.settings-section-title','.appearance-samples','.wallpaper-grid'):
            self.assertIn(selector, css)

    def test_dock_uses_mac_like_glass_and_original_colored_icon_system(self):
        css = HOME_CSS_PATH.read_text(encoding='utf-8').replace(' ', '')
        self.assertIn('.mac-dock{', css)
        self.assertIn('backdrop-filter:blur(14px)saturate(1.25)', css)
        self.assertIn('.mac-dock.lz-symbol', css)
        self.assertIn('fill:none', css)
        self.assertIn('stroke:currentColor', css)
        for family in ('launcher','agreement','rooms','queries','reviews','banking','settings'):
            selector = '.mac-dock-launcher' if family == 'launcher' else f'.dock-{family}'
            self.assertIn(selector, css)
        self.assertIn('--dock-dot:', css)
        self.assertIn('.dock-settings::before', css)

    def test_dock_magnification_uses_neighbor_field_without_layout_animation(self):
        js = HOME_JS_PATH.read_text(encoding='utf-8').replace(' ', '')
        self.assertIn('d/112', js)
        self.assertIn('influence*.36', js)
        self.assertIn('influence*12', js)
        self.assertNotIn('style.width=', js)
        self.assertNotIn('style.height=', js)

    def test_settings_dock_uses_same_livenza_symbol_stroke_contract(self):
        css = SETTINGS_CSS_PATH.read_text(encoding='utf-8').replace(' ', '')
        self.assertIn('.mac-dock.lz-symbol', css)
        self.assertIn('fill:none', css)
        self.assertIn('stroke:currentColor', css)


if __name__ == '__main__':
    unittest.main()
