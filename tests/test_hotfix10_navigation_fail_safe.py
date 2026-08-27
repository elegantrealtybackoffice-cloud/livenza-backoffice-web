from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=(ROOT/"templates/base.html").read_text(encoding="utf-8")
DASH=(ROOT/"templates/dashboard.html").read_text(encoding="utf-8")
HOME_JS=(ROOT/"static/home_light.js").read_text(encoding="utf-8")

class Hotfix10NavigationFailSafe(unittest.TestCase):
    def test_suites_controls_have_server_fallback_href(self):
        self.assertIn("href=\"{{url_for('dashboard',suites=1)}}\"", DASH)
        self.assertIn("href=\"{{url_for('dashboard',suites=1)}}\"", BASE)
    def test_server_can_open_drawer_without_home_js(self):
        self.assertIn("request.args.get('suites') == '1'", BASE)
        self.assertIn('suites_fallback_open', BASE)
    def test_runtime_exposes_ready_marker(self):
        self.assertIn("dataset.homeRuntime='ready'", HOME_JS)
        self.assertIn('data-home-runtime-watchdog', BASE)

if __name__=='__main__': unittest.main()
