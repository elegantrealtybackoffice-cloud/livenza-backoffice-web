from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT/'static/macos27_system.css').read_text(encoding='utf-8')
JS = (ROOT/'static/macos27_shell.js').read_text(encoding='utf-8')
APPS = (ROOT/'templates/_application_groups.html').read_text(encoding='utf-8')
SYMBOLS = (ROOT/'templates/_livenza_symbols.html').read_text(encoding='utf-8')
APP = (ROOT/'app.py').read_text(encoding='utf-8')
BASE = (ROOT/'templates/base.html').read_text(encoding='utf-8')
DASH = (ROOT/'templates/dashboard.html').read_text(encoding='utf-8')

class Hotfix8VisualContracts(unittest.TestCase):
    def test_svg_symbols_have_global_stroke_contract(self):
        self.assertRegex(CSS, r'\.lz-symbol\s*\{[^}]*fill\s*:\s*none[^}]*stroke\s*:\s*currentColor')

    def test_dock_icon_markup_is_endpoint_aware(self):
        self.assertIn('data-app-icon', APPS)
        self.assertIn('data-app-endpoint', APPS)

    def test_registry_has_visual_families(self):
        for token in ("'family':", "'accent':", "'accent2':"):
            self.assertIn(token, APP)

    def test_window_receives_visual_identity(self):
        for token in ('data-window-family', 'data-window-accent', 'data-window-accent2'):
            self.assertIn(token, JS)

    def test_core_apps_have_explicit_suite_selectors(self):
        for endpoint in ('agreements','rooms','tenants','queries','reviews','video_wall','food','billing','banking_suite','electricity_studio','letterhead_studio','settings_page'):
            self.assertIn(f'data-window-app="{endpoint}"', CSS)

    def test_suite_accent_tokens_exist(self):
        for token in ('--suite-accent:', '--suite-accent-2:', '--suite-soft:', '--suite-ink:'):
            self.assertIn(token, CSS)

    def test_content_reveal_motion_exists(self):
        self.assertIn('@keyframes mac-suite-content-in', CSS)
        self.assertIn('mac-suite-content-in', CSS)

    def test_reduced_motion_disables_suite_motion(self):
        self.assertRegex(CSS, r'prefers-reduced-motion[^}]*')
        self.assertIn('mac-suite-content-in', CSS)
        self.assertIn('animation:none!important', CSS)

    def test_no_hotfix8_stylesheet_was_added(self):
        self.assertNotIn('hotfix8.css', BASE.lower())

    def test_dashboard_suggestions_use_app_icon_component(self):
        self.assertIn('suggestion-app-icon', DASH)

    def test_dock_does_not_render_unavailable_apps_directly(self):
        self.assertIn('for app_item in dock_apps', APPS)
        self.assertNotRegex(APPS, r'render_dock_apps[\s\S]{0,800}app_item\(surface')

    def test_window_content_has_suite_surface_class(self):
        self.assertIn('mac-suite-surface', JS)

    def test_window_loading_uses_suite_accent(self):
        self.assertIn('var(--suite-accent)', CSS)

    def test_window_titlebar_has_suite_tint(self):
        self.assertIn('.mac-app-window.is-active .mac-window-titlebar::after', CSS)

    def test_no_blank_default_svg_fill(self):
        self.assertIn('stroke-linecap:round', CSS)
        self.assertIn('stroke-linejoin:round', CSS)

    def test_retired_presentation_assets_are_removed(self):
        for rel in (
            'static/style.css','static/desktop_v2701.css','static/desktop_v2701.js',
            'static/theme_v190_macos_light.css','static/shell_v190.css','static/shell_v190.js',
            'static/motion_v190.css','static/settings_v190.css','static/settings_v190.js',
        ):
            self.assertFalse((ROOT/rel).exists(), rel)

    def test_letterhead_assets_are_route_scoped(self):
        self.assertIn("request.endpoint.startswith('letterhead')", BASE)

    def test_ambient_loops_do_not_use_unpaused_intervals(self):
        app_js=(ROOT/'static/app.js').read_text(encoding='utf-8')
        self.assertNotIn('setInterval(performMascotAmbientAction', app_js)
        self.assertIn('document.hidden', app_js)
        self.assertNotIn('nudgeTimer=window.setInterval', app_js)

    def test_footer_clock_does_not_run_hidden_interval(self):
        app_js=(ROOT/'static/app.js').read_text(encoding='utf-8')
        self.assertNotIn('setInterval(updateFooterClock', app_js)
        self.assertIn('scheduleFooterClock', app_js)
        self.assertIn('document.hidden', app_js)

    def test_video_wall_player_polling_pauses_when_hidden(self):
        wall=(ROOT/'templates/wall_player.html').read_text(encoding='utf-8')
        self.assertNotIn('setInterval(sync', wall)
        self.assertNotIn('setInterval(beat', wall)
        self.assertIn('scheduleWallSync', wall)
        self.assertIn('scheduleWallBeat', wall)
        self.assertIn('document.hidden', wall)

    def test_home_date_line_box_is_not_tighter_than_glyph(self):
        self.assertRegex(CSS, r'\.home-widget-heading strong\{[^}]*line-height:38px')

    def test_stat_values_do_not_wrap(self):
        self.assertRegex(CSS, r'\.stats[^}]*b[^}]*\{[^}]*white-space:nowrap')

    def test_diagnostics_points_to_authoritative_theme(self):
        self.assertIn("static','macos27_system.css'", APP)
        self.assertNotIn("static','style.css'", APP)

    def test_mascot_has_no_temperature_badge(self):
        self.assertNotIn('mascot-weather-chip', BASE)

    def test_wallpaper_library_is_rich_and_original(self):
        wall=(ROOT/'templates/settings/_wallpaper.html').read_text(encoding='utf-8')
        for variant in ('aurora','spectrum','sequoia','midnight','livenza-blue','violet-glass','ocean','sunrise'):
            self.assertIn(f'data-wallpaper-value="{variant}"', wall)
            self.assertIn(variant, JS)
            self.assertIn(f'data-wallpaper="{variant}"', CSS)

    def test_all_suite_families_have_canvas_identity(self):
        for family in ('productivity','occupancy','pipeline','reputation','creative','hospitality','finance','utilities','communication','documents','system'):
            self.assertIn(f'data-window-family="{family}"', CSS)

if __name__ == '__main__':
    unittest.main()
