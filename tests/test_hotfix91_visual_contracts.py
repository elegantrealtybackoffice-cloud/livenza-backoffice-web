from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT/'templates/base.html').read_text(encoding='utf-8')
APPJS = (ROOT/'static/app.js').read_text(encoding='utf-8')
SHELLJS = (ROOT/'static/macos27_shell.js').read_text(encoding='utf-8')
CSS = (ROOT/'static/macos27_system.css').read_text(encoding='utf-8')
TV = (ROOT/'static/tv_compat.js').read_text(encoding='utf-8')
AUTO = (ROOT/'templates/settings/_automations.html').read_text(encoding='utf-8')
CTRL = (ROOT/'templates/settings/_control_centre.html').read_text(encoding='utf-8')
FOCUS = (ROOT/'templates/settings/_focus.html').read_text(encoding='utf-8')
APPEARANCE = (ROOT/'templates/settings/_appearance.html').read_text(encoding='utf-8')
APP = (ROOT/'app.py').read_text(encoding='utf-8')

class Hotfix91VisualContracts(unittest.TestCase):
    def test_marquee_removed_from_global_shell(self):
        for token in ('operations-marquee','liveOperationsMarquee','liveMarqueeTrack','marquee-live-label'):
            self.assertNotIn(token, BASE)

    def test_marquee_client_polling_removed(self):
        for token in ('/api/marquee','liveMarqueeTrack','renderTicker','restartMarqueeAnimation','marquee-loop-group'):
            self.assertNotIn(token, APPJS)
        self.assertNotIn("'control.marquee'", SHELLJS)
        self.assertNotIn("'focus.marquee'", SHELLJS)
        self.assertNotIn('liveOperationsMarquee', TV)

    def test_marquee_controls_removed_from_settings(self):
        for text in ('Marquee Status Builder','Show live marquee','LIVE RUNNING BAR','marquee-settings','marquee_show_'):
            self.assertNotIn(text, AUTO)
        self.assertNotIn('control.marquee', CTRL)
        self.assertNotIn('Live status', CTRL)
        self.assertNotIn('focus.marquee', FOCUS)
        self.assertNotIn('live-status strip', FOCUS)

    def test_marquee_backend_endpoint_and_runtime_context_removed(self):
        self.assertNotIn("@app.route('/api/marquee')", APP)
        self.assertNotIn('def marquee_status(', APP)
        self.assertNotIn('def live_marquee_items(', APP)
        self.assertNotIn('marquee_enabled=', APP)

    def test_automatic_appearance_no_longer_forces_dark_from_device(self):
        self.assertNotRegex(CSS, r'@media\(prefers-color-scheme:dark\)\s*\{\s*html\[data-appearance="auto"\]')
        self.assertNotIn('data-value="auto"', APPEARANCE)
        self.assertIn("const mode = ['light', 'dark'].includes", SHELLJS)

    def test_explicit_dark_mode_uses_graphite_not_black_canvas(self):
        dark = re.search(r'html\[data-appearance="dark"\]\s*\{([^}]*)\}', CSS)
        self.assertIsNotNone(dark)
        block = dark.group(1).lower()
        self.assertNotIn('--mac-content:#151515', block)
        self.assertNotIn('--mac-window:#1e1e1e', block)
        self.assertRegex(block, r'--mac-content:\s*#[23][0-9a-f]{5}')

    def test_suite_cards_have_vibrant_tinted_material(self):
        self.assertIn('--suite-card-vibrance:', CSS)
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) #appMain\s*\{[^}]*--suite-card-vibrance')
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) #appMain :is\([^}]+\)\{[^}]*linear-gradient')

    def test_electricity_has_warm_utility_palette_and_readable_surfaces(self):
        self.assertRegex(CSS, r'body:is\(\[data-page="electricity_studio"\][^}]+#appMain\{[^}]*--suite-accent:#f5b928')
        self.assertIn('--suite-accent-3:#4fcf9b', CSS)

    def test_route_toolbar_is_glass_not_dark_slab(self):
        match = re.search(r'\.mac-toolbar\.mac-route-toolbar\s*\{([^}]*)\}', CSS)
        self.assertIsNotNone(match)
        block = match.group(1).lower()
        self.assertIn('backdrop-filter', block)
        self.assertNotIn('background:#1e1e1e', block)
        self.assertNotIn('background:#222', block)

if __name__ == '__main__':
    unittest.main()
