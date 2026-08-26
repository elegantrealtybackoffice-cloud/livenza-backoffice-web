from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MacDesktopUiContractTests(unittest.TestCase):
    def text(self, relative):
        return (ROOT / relative).read_text(encoding='utf-8')

    def test_dashboard_has_desktop_widgets(self):
        html = self.text('templates/dashboard.html')
        self.assertIn('mac-desktop-home', html)
        self.assertIn('home-widget-stack', html)
        self.assertIn('home-weather-temperature', html)
        self.assertIn('home-suggestions-widget', html)
        self.assertIn('data-home-companion-open', html)

    def test_dock_renders_individual_suite_apps(self):
        base = self.text('templates/base.html')
        groups = self.text('templates/_application_groups.html')
        self.assertIn("appgroups.render_dock_apps()", base)
        self.assertIn("macro render_dock_apps", groups)
        self.assertIn("data-dock-app", groups)
        self.assertIn("Agreement Studio", groups)
        self.assertIn("Letterhead Studio", groups)

    def test_vibrant_desktop_styles_are_loaded_last(self):
        base = self.text('templates/base.html')
        self.assertIn("desktop_v2701.css", base)
        self.assertIn("desktop_v2701.js", base)
        css = self.text('static/desktop_v2701.css')
        self.assertIn("livenza_liquid_wallpaper.webp", css)
        self.assertIn('body[data-page="dashboard"] .mac-dock', css)
        self.assertIn('--desktop-violet', css)
        self.assertIn('position:fixed', css.replace(' ', ''))

    def test_home_script_updates_live_widget_content(self):
        js = self.text('static/desktop_v2701.js')
        self.assertIn('/api/companion/pulse', js)
        self.assertIn('homeWeatherTemperature', js)
        self.assertIn('homeCurrentTime', js)

    def test_macos27_kit_metrics_are_declared(self):
        css = self.text('static/desktop_v2701.css')
        for token in (
            '--mac-menu-bar-height:34px',
            '--mac-dock-height:58px',
            '--mac-sidebar-width:256px',
            '--mac-body-size:13px',
            '--mac-title1-size:22px',
            '--mac-notification-width:344px',
            '--mac-menu-item-height:24px',
        ):
            self.assertIn(token, css.replace(' ', ''))

    def test_home_uses_desktop_menu_bar(self):
        html = self.text('templates/dashboard.html')
        self.assertIn('mac-desktop-menubar', html)
        self.assertIn('homeCurrentTime', html)
        self.assertIn('homeCurrentDate', html)

    def test_version_metadata_describes_macos27_desktop(self):
        app = self.text('app.py')
        self.assertIn("'vibrant-macos27-desktop'", app)
        self.assertIn("'individual-suite-dock'", app)
        self.assertNotIn("'warm-neutral-liquid-glass'", app)
        self.assertNotIn("'single-suites-launcher'", app)

    def test_macos27_material_and_radius_tokens_match_kit(self):
        css = self.text('static/desktop_v2701.css').replace(' ', '')
        for token in (
            '--mac-window-radius:16px',
            '--mac-notification-radius:20px',
            '--mac-notification-blur:15px',
            '--mac-menu-blur:20px',
            '--mac-regular-glass-blur:30px',
            '--mac-menu-width:160px',
        ):
            self.assertIn(token, css)
        self.assertIn('border-radius:var(--mac-notification-radius)', css)

if __name__ == '__main__':
    unittest.main()
